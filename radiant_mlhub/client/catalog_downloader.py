import csv
import os
import threading
import tarfile
import sqlite3
import json
from glob import iglob

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from io import TextIOWrapper
from logging import getLogger
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union, Any
from urllib.parse import urlparse
from dateutil.parser import parse as date_parser

from pydantic import BaseModel
from shapely.geometry import box, shape
from tqdm import tqdm

from ..if_exists import DownloadIfExistsOpts
from ..session import Session
from .resumable_downloader import ResumableDownloader

log = getLogger(__name__)

JsonDict = Dict[str, Any]
GeoJSON = JsonDict

COMMON_ASSET_NAMES = [
    'documentation',
    'readme',
    'test_split',
    'train_split',
    'validation_split',
]
"""Common assets will be put into `_common` and only downloaded once."""


class CatalogDownloaderConfig(BaseModel):
    """
    Configuration model & validator for CatalogDownloader.
    """
    class Config:
        arbitrary_types_allowed = True

    api_key: Optional[str] = None
    bbox: Optional[Union[Tuple[float], List[float]]] = None
    catalog_only: bool = False
    collection_filter: Optional[Dict[str, List[str]]] = None
    dataset_id: str
    if_exists: DownloadIfExistsOpts = DownloadIfExistsOpts.resume
    intersects: Optional[GeoJSON] = None
    output_dir: Path
    profile: Optional[str] = None
    session: Session
    temporal_query: Optional[Union[datetime, Tuple[datetime, datetime]]] = None


class AssetRecord(BaseModel):
    """
    A stac_assets db record.
    """
    class Config:
        arbitrary_types_allowed = True
    rowid: Optional[int] = None
    asset_key: Optional[str] = None
    asset_save_path: Optional[str] = None
    asset_url: Optional[str] = None
    bbox_json: Optional[str] = None
    collection_id: Optional[str] = None
    common_asset: bool = False
    single_datetime: Optional[datetime] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    filtered: bool = False
    geometry_json: Optional[str] = None
    item_id: Optional[str] = None


class CatalogDownloader():

    config: CatalogDownloaderConfig
    err_report: TextIOWrapper
    err_report_path: Path
    catalog_file: Path
    work_dir: Path
    db_conn: sqlite3.Connection
    db_cur: sqlite3.Cursor

    def __init__(self, config: CatalogDownloaderConfig):
        if config.bbox is not None and config.intersects is not None:
            raise ValueError('Provider either bbox or intersects option (not both')
        if config.intersects:
            if 'geometry' not in config.intersects:
                raise ValueError('intersects must be geojson with a geometry property')
        self.config = config
        self.work_dir = (config.output_dir / config.dataset_id)
        self.work_dir.mkdir(exist_ok=True, parents=True)
        self.err_report_path = self.work_dir / 'err_report.csv'

    def _fetch_unfiltered_count(self) -> int:
        self.db_cur.execute(
            """
                SELECT COUNT(DISTINCT asset_save_path)
                    FROM assets WHERE filtered = 0
            """
        )
        (total_count, ) = self.db_cur.fetchone()
        return int(total_count)

    def _mark_asset_filtered(self, row_id: int) -> None:
        self.db_cur.execute(
            """
                UPDATE assets
                    SET filtered = 1
                    WHERE rowid = ?
            """,
            [row_id]
        )
        self.db_conn.commit()

    def _fetch_catalog_step(self) -> None:
        """
        Fetch the stac catalog archive, save to disk.
        Sets path to stac catalog .tar.gz.
        """
        c = self.config
        out_file = c.output_dir / f'{c.dataset_id}.tar.gz'
        dl = ResumableDownloader(
            session=c.session,
            url=f'/catalog/{c.dataset_id}',
            out_file=out_file,
            if_exists=c.if_exists,
            desc=f'{c.dataset_id}: fetch stac catalog',
            disable_progress_bar=False,
        )
        dl.run()
        assert out_file.exists()
        self.catalog_file = out_file

    def _unarchive_catalog_step(self) -> None:
        """
        Unarchive the stac catalog archive .tar.gz.
        In `skip` or `resume` mode, will not overwrite existing files.
        """
        c = self.config
        msg = f'unarchive {self.catalog_file.name}'
        log.info(msg)
        with tarfile.open(self.catalog_file, 'r:gz') as archive:
            if self.config.if_exists == DownloadIfExistsOpts.overwrite:
                archive.extractall(path=c.output_dir)
            else:
                members = archive.getmembers()
                for tar_info in tqdm(members, desc=msg):
                    if (c.output_dir / tar_info.name).exists():
                        continue
                    else:
                        archive.extract(tar_info, path=c.output_dir)
        assert (self.work_dir / 'catalog.json').exists()

    def _create_asset_list_step(self) -> None:
        """
        Scan the stac catalog and extract asset list into tabular format.
        Creates table in sqlite db.
        """
        msg = 'create stac asset list'
        log.info(msg)

        def _asset_save_path(rec: AssetRecord) -> Path:
            """
            Transform asset into a local save path. This filesystem layout
            is the same as the mlhub's collection archive .tar.gz files.
            """
            c = self.config
            ext = Path(str(urlparse(rec.asset_url).path)).suffix
            base_path = c.output_dir / c.dataset_id / rec.collection_id  # type: ignore
            asset_filename = f'{rec.asset_key}{ext}'
            if rec.item_id is None:
                # this is a collection level asset
                return base_path / asset_filename
            if rec.common_asset:
                # common assets: save to _common dir (at the collection level) instead of in every item subdir.
                return base_path / '_common' / asset_filename
            return base_path / rec.item_id / asset_filename

        def _insert_asset_rec(rec: AssetRecord) -> None:
            self.db_cur.execute(
                """
                    INSERT INTO assets (
                        collection_id,
                        item_id,
                        asset_key,
                        asset_url,
                        asset_save_path,
                        filtered,
                        common_asset,
                        bbox_json,
                        geometry_json,
                        single_datetime,
                        start_datetime,
                        end_datetime
                    ) VALUES (
                        :collection_id,
                        :item_id,
                        :asset_key,
                        :asset_url,
                        :asset_save_path,
                        :filtered,
                        :common_asset,
                        :bbox_json,
                        :geometry_json,
                        :single_datetime,
                        :start_datetime,
                        :end_datetime
                    );
                """,
                rec.dict()
            )
            self.db_conn.commit()

        def _handle_item(stac_item: JsonDict) -> None:
            item_id = stac_item['id']
            assets = stac_item['assets']
            props = stac_item['properties']
            common_meta = props.get('common_metadata', dict())
            bbox = stac_item.get('bbox', None)
            geometry = stac_item.get('geometry', None)
            if geometry and not bbox:
                raise RuntimeError(f'item {item_id} has no bbox, but has geometry')

            for k, v in assets.items():
                rec = AssetRecord(
                    collection_id=stac_item['collection'],
                    item_id=item_id,
                    asset_key=k,
                    common_asset=k in COMMON_ASSET_NAMES,
                    asset_url=v['href'],
                    bbox_json=json.dumps(bbox) if bbox else None,
                    geometry_json=json.dumps(geometry) if geometry else None,
                    single_datetime=props.get('datetime', None),
                    start_datetime=common_meta.get('start_datetime', None),
                    end_datetime=common_meta.get('end_datetime', None),
                )
                asset_save_path = _asset_save_path(rec).relative_to(self.work_dir)
                rec.asset_save_path = str(asset_save_path)
                _insert_asset_rec(rec)

        def _handle_collection(stac_collection: JsonDict) -> None:
            collection_id = stac_collection['id']
            assets = stac_collection.get('assets', None)
            if assets is None:
                return
            for k, v in assets.items():
                rec = AssetRecord(
                    collection_id=collection_id,
                    asset_key=k,
                    asset_url=v['href'],
                )
                asset_save_path = _asset_save_path(rec).relative_to(self.work_dir)
                rec.asset_save_path = str(asset_save_path)
                _insert_asset_rec(rec)

        json_srcs = iglob(str(self.work_dir / '**/*.json'), recursive=True)
        for json_src in json_srcs:
            p = Path(json_src)
            if p.name == 'catalog.json':
                continue
            with open(json_src) as json_fh:
                stac_item = json.load(json_fh)
                stac_type = stac_item.get('type', None)
                if p.name == 'collection.json' or stac_type == 'Collection':
                    _handle_collection(stac_item)
                else:
                    _handle_item(stac_item)
        log.info(f'{self._fetch_unfiltered_count()} unique assets in stac catalog.')

    def _filter_collections_step(self) -> None:
        """
        Iterate through the filters and mark entries in the assets table as `filtered`.
        Filter is an allow-list. Only matching collection_ids and optionally, asset keys,
        will be included.
        """
        f = self.config.collection_filter
        if f is None:
            return

        desc = 'filter by collection ids and asset keys'
        log.info(desc)

        total_asset_ct = self._fetch_unfiltered_count()
        self.db_cur.execute(
            """
                SELECT rowid, collection_id, asset_key
                    FROM assets
                    WHERE filtered = 0 AND item_id IS NOT NULL
            """
        )
        progress = tqdm(total=total_asset_ct, desc=desc)
        progress_value = 0
        row_ids_to_filter = set()
        while True:
            rows = self.db_cur.fetchmany()
            if not rows:
                progress.update(total_asset_ct)
                break

            progress_value += len(rows)
            progress.update(progress_value)

            for row_tuple in rows:
                (row_id, collection_id, asset_key) = row_tuple
                filtered = True
                if collection_id in f:
                    # collection_id is a key in the filter (allow list)
                    filter_asset_keys = f[collection_id]
                    if not filter_asset_keys:
                        # no asset keys, so include because of collection id
                        filtered = False
                    else:
                        # check each asset key
                        if asset_key in filter_asset_keys:
                            # include asset because it's key appears in filter (allow list)
                            filtered = False
                if filtered:
                    row_ids_to_filter.add(row_id)

        for row_id in row_ids_to_filter:
            self._mark_asset_filtered(row_id)

        total_asset_ct = self._fetch_unfiltered_count()
        if total_asset_ct == 0:
            raise RuntimeError(
                f'after filtering collections_ids and asset keys, zero assets to download. filter: {filter}'
            )
        log.info(f'{total_asset_ct} assets after collection filter.')

    def _filter_bbox_step(self) -> None:
        """
        Filter items by bounding box intersection. Marks items in the assets
        table as `filtered` if they do not intersect.

        """
        desc = 'filter by bounding box'
        if self.config.bbox is None:
            return
        bbox_polygon_query = box(*self.config.bbox)
        log.info(desc)

        total_asset_ct = self._fetch_unfiltered_count()
        self.db_cur.execute(
            """
                SELECT rowid, item_id, bbox_json
                    FROM assets
                    WHERE filtered = 0 AND item_id IS NOT NULL
                    ORDER BY item_id
            """
        )
        progress = tqdm(total=total_asset_ct, desc=desc)
        progress_value = 0
        row_ids_to_filter = set()

        while True:
            rows = self.db_cur.fetchmany()
            if not rows:
                progress.update(total_asset_ct)
                break

            progress_value += len(rows)
            progress.update(progress_value)

            # cache the bboxs, which belong to items, not to the asset. the
            # results are ordered by item_id, and since we're within
            # db_cur.fetchmany(), this is a cache with bounded size.
            item_bbox_cache: Dict[str, bool] = dict()

            for row_tuple in rows:
                (row_id, item_id, bbox_json) = row_tuple
                if not bbox_json:
                    log.warning(f'item missing bbox: {item_id}')
                    continue
                hit = item_bbox_cache.get(item_id, None)
                if hit is None:
                    bbox = json.loads(bbox_json)
                    item_bbox_polygon = box(*bbox)
                    hit = bbox_polygon_query.intersects(item_bbox_polygon)
                    item_bbox_cache[item_id] = hit
                if not hit:
                    row_ids_to_filter.add(row_id)

        for row_id in row_ids_to_filter:
            self._mark_asset_filtered(row_id)

        total_asset_ct = self._fetch_unfiltered_count()
        if total_asset_ct == 0:
            raise RuntimeError(
                f'after filtering by bounding box, zero assets to download. filter: {filter}'
            )
        log.info(f'{total_asset_ct} assets after bounding box filter.')

    def _filter_intersects_step(self) -> None:
        """
        Filter items by geojson vs. bounding box intersection.
        Marks items in the assets table as `filtered` if they do not intersect.
        """
        f = self.config.intersects
        if f is None:
            return

        desc = 'filter by intersects'
        log.info(desc)

        intersects_shape_query = shape(f['geometry'])

        total_asset_ct = self._fetch_unfiltered_count()
        self.db_cur.execute(
            """
                SELECT rowid, item_id, bbox_json
                    FROM assets
                    WHERE filtered = 0 AND item_id IS NOT NULL
                    ORDER BY item_id
            """
        )

        progress = tqdm(total=total_asset_ct, desc=desc)
        progress_value = 0
        row_ids_to_filter = set()
        while True:
            rows = self.db_cur.fetchmany()
            if not rows:
                progress.update(total_asset_ct)
                break

            progress_value += len(rows)
            progress.update(progress_value)

            # cache the spatial join test, which belong to items, not to the
            # asset. the results are ordered by item_id, and since we're within
            # db_cur.fetchmany(), here we maintain a cache with bounded size.
            item_intersects_cache: Dict[str, bool] = dict()

            for row_tuple in rows:
                (row_id, item_id, bbox_json) = row_tuple
                if not bbox_json:
                    log.warning(f'item missing bbox: {item_id}')
                    continue
                hit = item_intersects_cache.get(item_id, None)
                if hit is None:
                    bbox = json.loads(bbox_json)
                    item_bbox_polygon = box(*bbox)
                    hit = intersects_shape_query.intersects(item_bbox_polygon)
                    item_intersects_cache[item_id] = hit
                if not hit:
                    row_ids_to_filter.add(row_id)

        for row_id in row_ids_to_filter:
            self._mark_asset_filtered(row_id)

        total_asset_ct = self._fetch_unfiltered_count()
        if total_asset_ct == 0:
            raise RuntimeError(
                f'after filtering by intersects, zero assets to download. filter: {filter}'
            )
        log.info(f'{total_asset_ct} assets after intersects filter.')

    def _filter_temporal_step(self) -> None:
        """
        Filter items by temporal query. Marks items in the assets table as
        `filtered` if they do not fall in the temporal range or single day.
        """

        def one_to_one_check(d1: datetime, d2: datetime) -> bool:
            """
            Compare day for each.
            """
            return d1.day == d2.day

        def one_to_range_check(d1: datetime, d2: Tuple[datetime, datetime]) -> bool:
            """
            Compare single datetime with date range.
            """
            (d2_start, d2_end) = d2
            return d1 >= d2_start and d1 <= d2_end

        def range_to_range_check(d1: Tuple[datetime, datetime], d2: Tuple[datetime, datetime]) -> bool:
            """
            Compare two date ranges.
            """
            (d1_start, d1_end) = d1
            (d2_start, d2_end) = d2
            if d1_start >= d2_start and d1_start <= d2_end:
                return True
            if d1_end >= d2_start and d1_start <= d2_end:
                return True
            return False

        q = self.config.temporal_query
        if q is None:
            return
        desc = 'filter by temporal query'
        log.info(desc)
        total_asset_ct = self._fetch_unfiltered_count()
        self.db_cur.execute(
            """
                SELECT rowid, item_id, single_datetime, start_datetime, end_datetime
                    FROM assets
                    WHERE filtered = 0 and item_id IS NOT NULL
            """
        )
        progress = tqdm(total=total_asset_ct, desc=desc)
        progress_value = 0
        row_ids_to_filter = set()
        while True:
            rows = self.db_cur.fetchmany()
            if not rows:
                progress.update(total_asset_ct)
                break

            progress_value += len(rows)
            progress.update(progress_value)

            for row_tuple in rows:
                (row_id, item_id, single_datetime, start_datetime, end_datetime) = row_tuple
                filtered = False
                # inspect the stac item for datetime properties
                if single_datetime:
                    # item has single date property
                    if isinstance(q, tuple):
                        filtered = not one_to_range_check(
                            date_parser(single_datetime),
                            q
                        )
                    else:
                        filtered = not one_to_one_check(
                            date_parser(single_datetime),
                            q
                        )
                else:
                    # item has date range properties
                    start = date_parser(start_datetime)
                    end = date_parser(end_datetime)
                    if not start or not end:
                        # cannot process date range, just skip forward and log a warning
                        log.warn(f'cannot compare to missing date range for: {item_id}')
                        next
                    if isinstance(q, tuple):
                        filtered = not range_to_range_check((start, end), q)
                    else:
                        filtered = not one_to_range_check(q, (start, end))
                if filtered:
                    row_ids_to_filter.add(row_id)

        for row_id in row_ids_to_filter:
            self._mark_asset_filtered(row_id)

        total_asset_ct = self._fetch_unfiltered_count()
        if total_asset_ct == 0:
            raise RuntimeError(
              f'after filtering by temporal query, zero assets to download. filter: {filter}'
            )
        log.info(f'{total_asset_ct} assets after temporal filter.')

    def _asset_download_step(self) -> None:
        """
        Download all assets assets table, which are not marked as filtered.
        Manage thread pool, build error_log.
        """

        def _download_asset_worker(
            asset_url: str,
            out_file: Path,
            if_exists: DownloadIfExistsOpts,
        ) -> None:
            """
            Download asset worker function (will be called in multithreaded context).
            Returns Path (out_file) on success, or raises Exception on error.

            Warning: if the asset url is scheme s3://, it will be transformed to
            https://{bucket_name}.s3.amazonaws.com .
            """
            log.debug(f'(thread id: {threading.get_ident()}) {asset_url} -> {out_file}')
            if not out_file.parent.exists():
                out_file.parent.mkdir(exist_ok=True, parents=True)
            if 's3://' in asset_url:
                # workaround for some datasets, e.g. spacenet
                # * use https instead of s3 (avoid adding boto3 dependency)
                # * use https://bucket.s3.amazonaws.com because the region is unknown
                u = urlparse(asset_url)
                bucket_name = u.netloc
                cleaned_url = asset_url.replace(
                    f's3://{bucket_name}',
                    f'https://{bucket_name}.s3.amazonaws.com'
                )
            else:
                cleaned_url = asset_url

            dl = ResumableDownloader(
                url=cleaned_url,
                out_file=out_file,
                if_exists=if_exists,
                desc=f'fetch {asset_url}'
            )
            dl.run()
            assert out_file.exists(), f'failed to create {out_file}'

        # create set of unique asset save paths to process in threads, to avoid
        # having subthreads attempt to write to same file (ex: with _common assets).
        self.db_cur.execute("""
            SELECT asset_save_path, asset_url, collection_id, item_id, asset_key
                FROM assets
                WHERE filtered = 0
        """)
        asset_list = list()
        uniq_asset_save_path = set()
        while True:
            rows = self.db_cur.fetchmany()
            if not rows:
                break
            for row_tuple in rows:
                (asset_save_path, asset_url, collection_id, item_id, asset_key) = row_tuple
                if asset_save_path not in uniq_asset_save_path:
                    asset_rec = AssetRecord(
                        asset_save_path=asset_save_path,
                        asset_url=asset_url,
                        collection_id=collection_id,  # TODO yank?
                        item_id=item_id,  # TODO: yank?
                        asset_key=asset_key,
                    )
                    asset_list.append(asset_rec)
                    uniq_asset_save_path.add(asset_save_path)

        if 'PYTEST_CURRENT_TEST' in os.environ:
            # vcr.py does not work multithreading `requests`, so bail out here
            # and consider it a 'dry run'.
            return

        self._finalize_db()

        with ThreadPoolExecutor() as executor:
            future_to_asset_record = {
                executor.submit(
                    _download_asset_worker, **dict(
                        asset_url=r.asset_url,
                        out_file=self.work_dir / r.asset_save_path,  # type: ignore
                        if_exists=self.config.if_exists,
                    )): r for r in asset_list
            }
            for future in tqdm(
                        as_completed(future_to_asset_record),
                        desc='download assets',
                        total=len(asset_list)
                    ):
                asset_rec = future_to_asset_record[future]
                try:
                    future.result()
                except Exception as e:
                    # write a line to err_report in the format:
                    # (Error code, Dataset ID, Collection ID, Item ID, Asset Key, Asset URL).
                    r = asset_rec
                    self.err_writer.writerow([
                        str(e), self.config.dataset_id, r.collection_id, r.item_id, r.asset_key, r.asset_url
                    ])
                    log.exception(e)

    def _init_db(self) -> None:
        db_path = self.work_dir / 'mlhub_stac_assets.db'
        if db_path.exists():
            db_path.unlink()
        self.db_conn = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self.db_cur = self.db_conn.cursor()
        self.db_cur.arraysize = 1024
        self.db_cur.execute("""
            CREATE TABLE assets (
                collection_id TEXT,
                item_id TEXT,
                asset_key TEXT,
                asset_url TEXT,
                asset_save_path TEXT,
                filtered BOOLEAN,
                common_asset BOOLEAN,
                bbox_json TEXT,
                geometry_json TEXT,
                single_datetime TEXT,
                start_datetime TEXT,
                end_datetime TEXT
            )
        """)

    def _finalize_db(self) -> None:
        if not self.config.catalog_only:
            self.db_cur.close()
            self.db_conn.close()

    def __call__(self) -> None:
        """
        Create and run functions for each processing step.
        """
        c = self.config
        self.err_report = open(self.err_report_path, 'w')
        self.err_writer = csv.writer(self.err_report, quoting=csv.QUOTE_MINIMAL)

        steps: List[Callable[[], None]] = []
        steps.append(self._fetch_catalog_step)
        steps.append(self._unarchive_catalog_step)

        if not c.catalog_only:

            self._init_db()

            steps.append(self._create_asset_list_step)

            # conditional step for collection/item key filter
            if c.collection_filter:
                steps.append(self._filter_collections_step)

            # conditional step for temporal filter
            if c.temporal_query:
                steps.append(self._filter_temporal_step)

            # conditional step for bounding box spatial filter
            if c.bbox:
                steps.append(self._filter_bbox_step)

            # conditional step for geojson spatial filter
            if c.intersects:
                steps.append(self._filter_intersects_step)

            # create final step for asset downloading
            steps.append(self._asset_download_step)

        # call each step
        for step in steps:
            step()

        # inspect the error report
        self.err_report.flush()
        self.err_report.close()
        if os.path.getsize(self.err_report_path) > 0:
            msg = f'asset download error(s) were logged to {self.err_report.name}'
            log.error(msg)
            raise IOError(msg)

        if c.catalog_only:
            log.info(f'catalog saved to {self.work_dir}')
        else:
            log.info(f'assets saved to {self.work_dir}')
