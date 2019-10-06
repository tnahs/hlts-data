import logging
import os
import pathlib
import shutil

from .errors import ApplicationError


log = logging.getLogger(__name__)


class Utilities:
    @staticmethod
    def delete_dir(path: pathlib.PosixPath) -> None:

        try:
            shutil.rmtree(path)
        except OSError:
            pass
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}")

    @staticmethod
    def make_dir(path: pathlib.PosixPath) -> None:

        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}")

    @staticmethod
    def copy_dir(src: pathlib.PosixPath, dest: pathlib.PosixPath) -> None:

        try:
            shutil.copytree(src, dest)
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}")


utilities = Utilities()
