"""Prepare the local embedding model and index before teaching; no LLM request."""

import os
from pathlib import Path

from dotenv import load_dotenv

from rag import get_engine


def main() -> None:
    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    data = Path(os.environ.get("BACKROOMS_DATA_DIR", root / "data"))
    storage = Path(os.environ.get("BACKROOMS_STORAGE_DIR", root / "storage"))
    get_engine(data, storage).prepare()
    print("Archive ready. The index and embedding model can be reused.")


if __name__ == "__main__":
    main()
