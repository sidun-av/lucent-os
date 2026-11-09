"""python3 -m lucent_settings.accent_sync: put the accent colour chosen in
Settings back if a light/dark switch (Auto at sunset) dropped it. Run by
lucent-settings-accent.path; does nothing when no accent was chosen."""

import sys

from .backends.appearance import sync_accent
from .run import Runner

if __name__ == "__main__":
    sync_accent(Runner())
    sys.exit(0)
