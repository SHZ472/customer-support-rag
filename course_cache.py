"""Place model data and runtime scratch files under the application cache."""

import os
from pathlib import Path
import tempfile

CACHE = Path(__file__).resolve().parent / ".cache"
for name, directory in {
    "HF_HOME": CACHE / "huggingface",
    "HF_HUB_CACHE": CACHE / "huggingface" / "hub",
    "TORCH_HOME": CACHE / "torch",
    "TMPDIR": CACHE / "tmp",
}.items():
    directory.mkdir(parents=True, exist_ok=True)
    os.environ[name] = str(directory)
tempfile.tempdir = os.environ["TMPDIR"]
