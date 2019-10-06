import logging
import pathlib
import sqlite3

from .defaults import AppleBooksDefaults
from .errors import AppleBooksError


log = logging.getLogger(__name__)


class AppleBooksDB:
    def query_sources_db(self):

        query = """
            SELECT
                ZBKLIBRARYASSET.ZASSETID as source_id,
                ZBKLIBRARYASSET.ZTITLE as source_name,
                ZBKLIBRARYASSET.ZAUTHOR as source_author,
                ZBKLIBRARYASSET.ZPATH as source_path
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
                ZANNOTATIONLOCATION as epubcfi,
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
        """ via https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory """

        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]

        return d
