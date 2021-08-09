import pathlib


def get_api_response(path: str) -> str:
    response_path = pathlib.Path(__file__).parent / "data" / path
    with response_path.open("r", encoding="utf-8") as src:
        return src.read()
