import json
import os
import sys
import pathlib
import shutil
import logging

from .applebooks import AppleBooks
from .defaults import AppDefaults
from .errors import ApplicationError


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


log = logging.getLogger(__name__)


class App:
    def __init__(self):

        self.utils = Utilities(self)
        self.config = Config(self)

        self._setup()

    def _setup(self):

        # Create app root_dir and day_dir directories.
        self.utils.make_dir(path=AppDefaults.root_dir)
        self.utils.make_dir(path=AppDefaults.day_dir)

    def run(self, args):

        if args.which == "applebooks":
            self.applebooks = AppleBooks(self)
            self.applebooks.run()


class Utilities:
    def __init__(self, app):

        self.app = app

    def delete_dir(self, path: pathlib.PosixPath) -> None:

        try:
            shutil.rmtree(path)
        except OSError:
            pass
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}")

    def make_dir(self, path: pathlib.PosixPath) -> None:

        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}")

    def copy_dir(self, src: pathlib.PosixPath, dest: pathlib.PosixPath) -> None:

        try:
            shutil.copytree(src, dest)
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}")


class Config:
    def __init__(self, app):

        self.app = app
        self._load()

    def _load(self):

        try:

            with open(AppDefaults.config_file, "r") as f:
                data = json.load(f)

                try:
                    self.tag_prefix = data["tag_prefix"]
                    self.collection_prefix = data["collection_prefix"]
                    self.starred_collection = data["starred_collection"]
                except KeyError as error:
                    self._load_error(error)
                    self._set_defaults()
                    self._save()
                except Exception as error:
                    raise ApplicationError(f"Unexpected Error: {repr(error)}")

        except json.JSONDecodeError as error:
            self._load_error(error)
            self._set_defaults()
            self._save()
        except FileNotFoundError:
            self._set_defaults()
            self._save()
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}")

    def _load_error(self, error):

        log.error(f"Error reading {AppDefaults.config_file}.\n{repr(error)}")

        config_file = AppDefaults.config_file
        config_file_bak = config_file.with_suffix(".bak")
        config_file.replace(config_file_bak)

    def _set_defaults(self):

        log.info(f"Setting {AppDefaults.name} to default configuration.")

        self.tag_prefix = "#"
        self.collection_prefix = "@"
        self.starred_collection = "star"

    def _save(self):

        log.info(f"Saving {AppDefaults.config_file}...")

        with open(AppDefaults.config_file, "w") as f:
            json.dump(self._serialize(), f, indent=4)

    def _serialize(self):

        config = {
            "tag_prefix": self.tag_prefix,
            "collection_prefix": self.collection_prefix,
            "starred_collection": self.starred_collection,
        }

        return config
