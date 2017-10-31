#!/usr/bin/env python3
import sys
from app import main


if __name__ == "__main__":
    sys.exit(main.run(sys.argv[1:]) or 0)


