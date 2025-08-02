from pathlib import Path

_CURRENT_FILE_DIR = Path(__file__).parent.absolute()

GALE_ROOT_DIR = _CURRENT_FILE_DIR.parent.parent.parent.absolute()
"""Root directory of the gale project; aka the manifest directory (NOT the west topdir, which is one level above)."""

WORKSPACE_DIR = GALE_ROOT_DIR.parent.absolute()
"""Directory where west shall pull all the projects and modules into."""

TOOLS_DIR = WORKSPACE_DIR / "tools"
"""Directory used by some Zephyr modules."""

BSIM_DIR = TOOLS_DIR / "bsim"
"""Directory used to build and use the BabbleSim tool."""
