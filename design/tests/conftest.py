import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# design/*.py (generators, tokens) and the runtime package /usr/lib/lucent/lucent_theme
sys.path[:0] = [str(ROOT / "design"), str(ROOT / "system_files/usr/lib/lucent")]
