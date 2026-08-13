"""Entry point for ``python -m hwdesign.labkit``."""
import sys

from hwdesign.labkit.publish import main

if __name__ == "__main__":
    sys.exit(main())
