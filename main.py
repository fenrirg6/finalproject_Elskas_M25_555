#!/usr/bin/env python3

import sys

from valutatrade_hub.cli.interface import run, run_interactive


def main():
    if len(sys.argv) > 1:
        sys.exit(run())
    else:
        run_interactive()

if __name__ == "__main__":
    main()