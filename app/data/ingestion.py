from pathlib import Path


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")


def get_raw_documents():
    """Return the documents currently available in the raw data folder."""

    return list(RAW_DATA_DIR.iterdir())


def prepare_data_directories():
    """Create required data directories if they do not exist."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)