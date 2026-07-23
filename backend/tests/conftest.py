import sys
from pathlib import Path


# Add backend root directory to Python path
backend_path = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(backend_path)
)