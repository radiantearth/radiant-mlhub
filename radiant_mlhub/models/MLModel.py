"""Extensions of the `PySTAC <https://pystac.readthedocs.io/en/latest/>`_ classes that provide convenience methods for interacting
with the `Radiant MLHub API <https://docs.mlhub.earth/#radiant-mlhub-api>`_."""

from __future__ import annotations
import concurrent.futures
from copy import deepcopy
from enum import Enum
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Union, cast

import pystac.collection
import pystac.catalog
import pystac.item
import pystac.link
import pystac.provider

from .. import client
from ..exceptions import EntityDoesNotExist


class MLModel(pystac.item.Item):
    """
    TODO: MLModel impl
    """
    def __init__(  # type: ignore[no-untyped-def]
        self,
        id,
    ):
        pass
    pass
