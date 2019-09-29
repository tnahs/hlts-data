import re
import json
import psutil
import pathlib
import sqlite3
import logging
from datetime import datetime

from .defaults import AppleBooksDefaults
from .errors import AppleBooksError


log = logging.getLogger(__name__)


class AppleBooks:
    def __init__(self, app):

        if self._is_applebooks_running():
            raise AppleBooksError("Apple Books currently running.")

        self.app = app
        self._setup()

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

    def run(self):

        self._copy_databases()
        self._cache_annotation_data()
        self._process_annotations()
        self._save_annotation_data()
        """
        self._process_sources()
        """

    def _setup(self):
        """ Build all relevant directories for AppleBooks. We don't create the
        directories for local_bklibrary_dir and local_aeannotation_dir seeing
        as these are created when the source databases are copied over. """

        # Delete local_root_dir. Just in case app is run more than once a day.
        self.app.utils.delete_dir(path=AppleBooksDefaults.local_root_dir)

        # Create local_root_dir and local_db_dir.
        self.app.utils.make_dir(path=AppleBooksDefaults.local_root_dir)
        self.app.utils.make_dir(path=AppleBooksDefaults.local_db_dir)

    def _copy_databases(self):
        """ Copy AppleBooks databases to local directory. """

        # Copy directory containing BKLibrary###.sqlite files.
        self.app.utils.copy_dir(
            src=AppleBooksDefaults.src_bklibrary_dir,
            dest=AppleBooksDefaults.local_bklibrary_dir,
        )

        # Copy directory containing AEAnnotation###.sqlite files.
        self.app.utils.copy_dir(
            src=AppleBooksDefaults.src_aeannotation_dir,
            dest=AppleBooksDefaults.local_aeannotation_dir,
        )

    def _cache_annotation_data(self):
        """ Query and cache database data. """

        db = AppleBooksDB(self.app)

        self._data_sources = db.query_sources_db()
        self._data_annotations = db.query_annotations_db()

    """
    def _process_sources(self):

        self._sources = []

        for _source in self._data_sources:

            source = Source(self.app, _source)

            for _annotation in self._data_annotations:

                if _annotation["source_id"] == _source["source_id"]:
                    _annotation["source_name"] = _source["source_name"]
                    _annotation["source_author"] = _source["source_author"]

                    annotation = Annotation(self.app, _annotation)

                    source.add_annotation(annotation)

            self._sources.append(source)
    """

    def _process_annotations(self):
        """ """

        self._annotations = []

        for _annotation in self._data_annotations:
            for _source in self._data_sources:
                if _annotation["source_id"] == _source["source_id"]:
                    _annotation["source_name"] = _source["source_name"]
                    _annotation["source_author"] = _source["source_author"]

            annotation = Annotation(self.app, _annotation)

            self._annotations.append(annotation)

    @property
    def _data(self):

        data = {
            "annotations": [annotation.serialize() for annotation in self._annotations],
            "metadata": {
                "date": datetime.utcnow().isoformat(),
                "count": len(self._annotations),
                "version": AppleBooksDefaults.version,
            },
        }

        return data

    def _save_annotation_data(self):
        """ """
        with open(AppleBooksDefaults.dump_json_file, "w") as f:
            json.dump(self._data, f, indent=4)


"""
class Source:
    def __init__(self, app, data: dict):

        self.app = app
        self.data = data

        self._annotations = []

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} - {self.author}>"

    def add_annotation(self, annotation):
        self._annotations.append(annotation)

    @property
    def has_annotations(self):
        return bool(len(self._annotations))

    @property
    def annotations(self):
        return self._annotations

    @property
    def id(self):
        return self.data.get("source_id")

    @property
    def name(self):
        return self.data.get("source_name")

    @property
    def author(self):
        return self.data.get("source_author")
"""


class Annotation:

    origin = AppleBooksDefaults.origin

    _notes = ""
    _tags = []
    _collections = []
    _is_starred = False

    def __init__(self, app, data: dict):

        self.app = app
        self.data = data

        self.tag_prefix = self.app.config.tag_prefix
        self.collection_prefix = self.app.config.collection_prefix
        self.starred_collection = self.app.config.starred_collection

        self.re_tags = re.compile(f"\B{self.tag_prefix}[^{self.tag_prefix}\s]+\s?")
        self.re_collections = re.compile(
            f"\B{self.collection_prefix}[^{self.collection_prefix}\s]+\s?"
        )

        self._process_notes()
        self._process_tags()
        self._process_collections()

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.id}>"

    def _process_tags(self):

        _notes = self.data.get("notes", "")

        if not _notes:
            return

        tags = re.findall(self.re_tags, _notes)
        tags = [t.strip() for t in tags]
        tags = [re.sub(self.tag_prefix, "", t) for t in tags]

        self._tags = tags

    def _process_collections(self):

        _notes = self.data.get("notes", "")

        if not _notes:
            return

        collections = re.findall(self.re_collections, _notes)
        collections = [c.strip() for c in collections]
        collections = [re.sub(self.collection_prefix, "", c) for c in collections]

        try:
            collections.remove(self.starred_collection)
        except ValueError:
            """ ValueError means the collections doest not contain the
            starred_collection therefore it was never 'starred'. """
            pass
        else:
            self._is_starred = True

        self._collections = collections

    def _process_notes(self):

        _notes = self.data["notes"]

        if not _notes:
            return

        # Remove tags and collections from notes.
        notes = re.sub(self.re_tags, "", _notes)
        notes = re.sub(self.re_collections, "", notes)
        notes = notes.strip()

        self._notes = notes

    def _convert_date(self, epoch: float) -> str:
        """ Converts Epoch to ISO861"""

        try:
            epoch = float(epoch)
        except TypeError:
            log.warning(f"Annotation {self.id} contains invalid date.")
            return None

        seconds_since_epoch = epoch + AppleBooksDefaults.ns_time_interval_since_1970

        date = datetime.utcfromtimestamp(seconds_since_epoch)
        date = date.isoformat()

        return date

    @staticmethod
    def _convert_style(index: int) -> str:
        """ Converts AppleBooks style index to style string. """
        return {
            0: "underline",
            1: "green",
            2: "blue",
            3: "yellow",
            4: "pink",
            5: "purple",
        }.get(index)

    @property
    def id(self):
        return self.data.get("id")

    @property
    def text(self):
        return self.data.get("text")

    @property
    def source_id(self):
        return self.data.get("source_id")

    @property
    def source_name(self):
        return self.data.get("source_name")

    @property
    def source_author(self):
        return self.data.get("source_author")

    @property
    def notes(self):
        return self._notes

    @property
    def tags(self):
        return self._tags

    @property
    def collections(self):
        return self._collections

    @property
    def date_created(self):
        return self._convert_date(self.data.get("date_created"))

    @property
    def date_modified(self):
        return self._convert_date(self.data.get("date_modified"))

    @property
    def style(self):
        return self._convert_style(self.data.get("style"))

    @property
    def location(self):
        return self.data.get("location")

    @property
    def is_starred(self):
        return self._is_starred

    def serialize(self):

        data = {
            "id": self.id,
            "text": self.text,
            "notes": self.notes,
            "source": {
                "id": self.source_id,
                "name": self.source_name,
                "author": self.source_author,
            },
            "tags": self.tags,
            "collections": self.collections,
            "metadata": {
                "date_created": self.date_created,
                "date_modified": self.date_modified,
                "style": self.style,
                "location": self.location,
                "origin": self.origin,
                "is_starred": self.is_starred,
            },
        }

        return data


class AppleBooksDB:
    def __init__(self, app):

        self.app = app

    def query_sources_db(self):

        query = """
            SELECT
                ZBKLIBRARYASSET.ZASSETID as source_id,
                ZBKLIBRARYASSET.ZTITLE as source_name,
                ZBKLIBRARYASSET.ZAUTHOR as source_author
            FROM ZBKLIBRARYASSET

            ORDER BY ZBKLIBRARYASSET.ZTITLE;
        """

        db = self._get_sqlite_file(path=AppleBooksDefaults.local_bklibrary_dir)
        data = self._execute_query(sqlite_file=db, query=query)

        return data

    def query_annotations_db(self):

        query = """
            SELECT
                ZAEANNOTATION.ZANNOTATIONASSETID as source_id,
                ZANNOTATIONUUID as id,
                ZANNOTATIONSELECTEDTEXT as text,
                ZANNOTATIONNOTE as notes,
                ZANNOTATIONSTYLE as style,
                ZANNOTATIONLOCATION as location,
                ZANNOTATIONCREATIONDATE as date_created,
                ZANNOTATIONMODIFICATIONDATE as date_modified

            FROM ZAEANNOTATION

            WHERE ZANNOTATIONSELECTEDTEXT IS NOT NULL
                AND ZANNOTATIONDELETED = 0

            ORDER BY ZANNOTATIONASSETID;
        """

        db = self._get_sqlite_file(path=AppleBooksDefaults.local_aeannotation_dir)
        data = self._execute_query(sqlite_file=db, query=query)

        return data

    def _get_sqlite_file(self, path: pathlib.Path) -> pathlib.Path:
        """ Glob full database path. """

        sqlite_file = list(path.glob("*.sqlite"))

        try:
            sqlite_file = sqlite_file[0]
            return sqlite_file
        except IndexError:
            raise AppleBooksError(f"Couldn't find AppleBooks database @ {path}.")
        except Exception as error:
            raise AppleBooksError(f"Unexpected Error: {repr(error)}")

    def _execute_query(self, sqlite_file, query) -> list:

        connection = self._connect_to_db(sqlite_file)

        with connection:
            cursor = connection.cursor()
            cursor.execute(query)
            data = cursor.fetchall()

        return data

    def _connect_to_db(self, sqlite_file: pathlib.Path) -> sqlite3.Connection:
        """ Create a database connection to SQLite database. """

        try:
            connection = sqlite3.connect(sqlite_file)
            connection.row_factory = self._dict_factory
            return connection
        except sqlite3.Error as error:
            raise AppleBooksError(f"SQLite Error: {repr(error)}")
        except Exception as error:
            raise AppleBooksError(f"Unexpected Error: {repr(error)}")

        return None

    def _dict_factory(self, cursor: sqlite3.Cursor, row: tuple) -> dict:

        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]

        return d
