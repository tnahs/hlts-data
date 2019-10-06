import logging
import sys

from .applebooks import AppleBooks
from .utilities import utilities
from .defaults import AppDefaults


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


log = logging.getLogger(__name__)


class App:
    def __init__(self):

        self._setup()

    def _setup(self) -> None:

        # Create app root_dir and day_dir directories.
        utilities.make_dir(path=AppDefaults.root_dir)
        utilities.make_dir(path=AppDefaults.day_dir)

    def run(self) -> None:

        self.applebooks = AppleBooks()
        self.applebooks.run()
