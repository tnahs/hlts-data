import logging
import re
from datetime import datetime

from ..config import config
from .defaults import AppleBooksDefaults


log = logging.getLogger(__name__)


TAG_PREFIX = config.tag_prefix
COLLECTION_PREFIX = config.collection_prefix
STARRED_COLLECTION = config.starred_collection

RE_TAGS = re.compile(f"\B{TAG_PREFIX}[^{TAG_PREFIX}\s]+\s?")
RE_COLLECTIONS = re.compile(f"\B{COLLECTION_PREFIX}[^{COLLECTION_PREFIX}\s]+\s?")


class Source:
    def __init__(self, data: dict):

        self._data = data

        self._annotations = []

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} by {self.author}>"

    def add_annotation(self, annotation):
        self._annotations.append(annotation)

    @property
    def has_annotations(self):
        return bool(len(self._annotations))

    @property
    def annotations(self):
        return sorted(self._annotations, key=lambda a: a.location)

    @property
    def id(self):
        return self._data.get("source_id")

    @property
    def name(self):
        return self._data.get("source_name")

    @property
    def author(self):
        return self._data.get("source_author")

    @property
    def path(self):
        return self._data.get("source_path")

    def serialize(self):

        data = {
            "id": self.id,
            "name": self.name,
            "author": self.author,
            "path": self.path,
            "annotations": [a.serialize(source=False) for a in self.annotations],
        }

        return data


class Annotation:

    origin = AppleBooksDefaults.name

    _notes = ""
    _tags = []
    _collections = []
    _is_starred = False

    def __init__(self, data: dict):

        self._data = data

        self._process()

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.text[:50].strip()}...>"

    def _process(self):

        for attr in dir(self):
            if attr.startswith("_process_"):
                getattr(self, attr)()

    def _process_text(self):

        _text = self._data.get("text", "")

        # Remove single and double curly quotes.
        _text = _text.replace("\u2018", "'").replace("\u2019", "'")
        _text = _text.replace("\u201c", '"').replace("\u201d", '"')
        # Strip trailing new lines and split into paragraphs.
        _text = _text.rstrip("\n").split("\n")
        # Strip trailing whitespace.
        _text = [t.strip() for t in _text]
        # Remove any empty items in list.
        _text = list(filter(None, _text))

        self._text = _text

    def _process_tags(self):

        _notes = self._data.get("notes", "")

        if not _notes:
            return

        _tags = re.findall(RE_TAGS, _notes)
        _tags = [t.strip() for t in _tags]
        _tags = [t.replace(TAG_PREFIX, "") for t in _tags]

        self._tags = _tags

    def _process_collections(self):

        _notes = self._data.get("notes", "")

        if not _notes:
            return

        _collections = re.findall(RE_COLLECTIONS, _notes)
        _collections = [c.strip() for c in _collections]
        _collections = [c.replace(COLLECTION_PREFIX, "") for c in _collections]

        try:
            _collections.remove(STARRED_COLLECTION)
        except ValueError:
            """ ValueError means _collections does not contain the
            starred_collection item therefore it was never 'starred'. """
            pass
        else:
            self._is_starred = True

        self._collections = _collections

    def _process_notes(self):

        _notes = self._data["notes"]

        if not _notes:
            return

        # Remove tags and collections from notes.
        _notes = re.sub(RE_TAGS, "", _notes)
        _notes = re.sub(RE_COLLECTIONS, "", _notes)
        _notes = _notes.strip()

        self.__notes = _notes

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

    @staticmethod
    def _parse_epubcfi(epubcfi: str):
        """ Starting with: epubcfi(/6/20[part01]!/4/182,/1:0,/3:23)
        via https://github.com/matttrent/ibooks-highlights/blob/master/ibooks_highlights/util.py#L20
        """

        # Captures one or more numbers after a slash /0 /00 /000 etc.
        RE_DIGITS = re.compile(r"\/(\d+)")

        if not epubcfi:
            return None

        # "/6/20[part01]!/4/182,/1:0,/3:23"
        core = epubcfi[8:-1]
        # ["/6/20[part01]!/4/182", "/1:0", "/3:23"]
        core_parts = core.split(",")
        # "/6/20[part01]!/4/182/1:0"
        head = core_parts[0] + core_parts[1]
        # ["/6/20[part01]!/4/182/1", "0"]
        head_parts = head.split(":")
        # [6, 20, 4, 182, 1]
        offsets = [int(x) for x in re.findall(RE_DIGITS, head_parts[0])]

        try:
            # [6, 20, 4, 182, 1, 0]
            offsets.append(int(head_parts[1]))
        except IndexError:
            pass

        # 0006.0020.0004.0182.0001.0000
        return ".".join([f"{i:04}" for i in offsets])

    @property
    def id(self):
        return self._data.get("id")

    @property
    def text(self):
        return self._text

    @property
    def source_id(self):
        return self._data.get("source_id")

    @property
    def source_name(self):
        return self._data.get("source_name")

    @property
    def source_author(self):
        return self._data.get("source_author")

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
        return self._convert_date(self._data.get("date_created"))

    @property
    def date_modified(self):
        return self._convert_date(self._data.get("date_modified"))

    @property
    def style(self):
        return self._convert_style(self._data.get("style"))

    @property
    def epubcfi(self):
        return self._data.get("epubcfi")

    @property
    def location(self):
        return self._parse_epubcfi(self._data.get("epubcfi"))

    @property
    def is_starred(self):
        return self._is_starred

    def serialize(self, source=True):

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
                "epubcfi": self.epubcfi,
                "location": self.location,
                "origin": self.origin,
                "is_starred": self.is_starred,
            },
        }

        if not source:
            del data["source"]

        return data
