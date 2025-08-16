# addresskit/utils/io.py
from pathlib import Path
<<<<<<< HEAD
def ensure_parent_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
=======
import os


def get_paths(input_dir=None, output_dir=None):
    kaggle_in = Path("/kaggle/input")
    kaggle_out = Path("/kaggle/working")

    if kaggle_in.exists():  # Kaggle ortamı
        base_in = Path(os.getenv("INPUT_DIR", kaggle_in))
        base_out = Path(os.getenv("OUTPUT_DIR", kaggle_out))
    else:  # Lokal
        base_in = Path(input_dir or "data/raw")
        base_out = Path(output_dir or "data/processed")

    base_out.mkdir(parents=True, exist_ok=True)
    return base_in, base_out
>>>>>>> f3a69242bb20942eb83b5471dc20cc8ed3b34b24
