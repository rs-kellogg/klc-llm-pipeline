from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # Python <=3.10


def load_config(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)

