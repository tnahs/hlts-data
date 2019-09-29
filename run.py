#!/usr/bin/env python3

import argparse
import sys

from app import App

"""
TODO: epubcfi
TODO: custom dump path
TODO: write pdf/txt file per source
TODO: exception handling
TODO: type annotate
"""

"""
Default directory is: ~/.hlts-data
Config file location: ~/.hlts-data/config.json

To run with Books:
- Close Books
- Run: python3 run.py applebooks
"""


app = App()


parser = argparse.ArgumentParser()
parser.add_argument("which", choices=["applebooks"])

args = parser.parse_args()


if __name__ == "__main__":

    app.run(args)
    sys.exit()
