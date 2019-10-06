import json
import logging

from .defaults import AppDefaults
from .errors import ApplicationError


log = logging.getLogger(__name__)


class Config:
    def __init__(self):

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


config = Config()
