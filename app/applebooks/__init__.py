import json
import logging
from datetime import datetime

import psutil

from ..utilities import utilities
from .db import AppleBooksDB
from .defaults import AppleBooksDefaults
from .errors import AppleBooksError
from .models import Annotation, Source


log = logging.getLogger(__name__)


class AppleBooks:
    def __init__(self):

        if self._is_applebooks_running():
            raise AppleBooksError("Apple Books currently running.")

        self._setup()

    def run(self):

        self._copy_databases()
        self._query_and_cache_data()
        self._process_data()
        self._save_data()

    @staticmethod
    def _is_applebooks_running():
        """ Check to see if AppleBooks is currently running. """

        for proc in psutil.process_iter():

            try:
                pinfo = proc.as_dict(attrs=["name"])
            except psutil.NoSuchProcess:
                """ When a process doesn't have a name it might mean it's a
                zombie process which ends up raising a NoSuchProcess exception
                or its subclass the ZombieProcess exception.
                """
                pass
            except Exception as error:
                raise AppleBooksError(f"Unexpected Error: {repr(error)}")

            if pinfo["name"] == "Books":
                return True

        return False

    def _setup(self):
        """ Build all relevant directories for AppleBooks. We don't create the
        directories for local_bklibrary_dir and local_aeannotation_dir seeing
        as these are created when the source databases are copied over. """

        # Delete local_root_dir. Just in case app is run more than once a day.
        utilities.delete_dir(path=AppleBooksDefaults.local_root_dir)

        # Create local_root_dir and local_db_dir.
        utilities.make_dir(path=AppleBooksDefaults.local_root_dir)
        utilities.make_dir(path=AppleBooksDefaults.local_db_dir)

    def _copy_databases(self):
        """ Copy AppleBooks databases to local directory. """

        # Copy directory containing BKLibrary###.sqlite files.
        utilities.copy_dir(
            src=AppleBooksDefaults.src_bklibrary_dir,
            dest=AppleBooksDefaults.local_bklibrary_dir,
        )

        # Copy directory containing AEAnnotation###.sqlite files.
        utilities.copy_dir(
            src=AppleBooksDefaults.src_aeannotation_dir,
            dest=AppleBooksDefaults.local_aeannotation_dir,
        )

    def _query_and_cache_data(self):
        """ Query and cache database data. """

        db = AppleBooksDB()

        self._query_data_sources = db.query_sources_db()
        self._query_data_annotations = db.query_annotations_db()

    def _process_data(self):

        self._sources = []
        self._annotations = []

        for _source in self._query_data_sources:

            source = Source(_source)

            for _annotation in self._query_data_annotations:
                if _annotation["source_id"] == _source["source_id"]:

                    _annotation["source_name"] = _source["source_name"]
                    _annotation["source_author"] = _source["source_author"]

                    annotation = Annotation(_annotation)
                    source.add_annotation(annotation)

                    self._annotations.append(annotation)

            if source.has_annotations:
                self._sources.append(source)

    def _save_data(self):
        """ """
        with open(AppleBooksDefaults.output_sources_file, "w") as f:
            json.dump(self._data_sources, f, indent=4)

        with open(AppleBooksDefaults.output_annotations_file, "w") as f:
            json.dump(self._data_annotations, f, indent=4)

    @property
    def _data_sources(self):

        data = {
            "sources": [s.serialize() for s in self._sources],
            "metadata": self._metadata,
        }

        return data

    @property
    def _data_annotations(self):

        data = {
            "annotations": [a.serialize() for a in self._annotations],
            "metadata": self._metadata,
        }

        return data

    @property
    def _metadata(self):

        metadata = {
            "date": datetime.utcnow().isoformat(),
            "count_sources": len(self._sources),
            "count_annotations": len(self._annotations),
            "version": AppleBooksDefaults.version,
        }

        return metadata
