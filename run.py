#!/usr/bin/env python3

import sys
import argparse

from app import App

"""
TODO: epubcfi
TODO: custom dump path
TODO: write pdf/txt file per source
TODO: exception handling
TODO: type annotate
"""

"""
Default directory is: ~/.hltsdump
Config file location: ~/.hltsdump/config.json
Log file location: ~/.hltsdump/app.log
Default dump directory is: ~/.hltsdump/dumps

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
