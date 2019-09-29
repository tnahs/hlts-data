from ..errors import ApplicationError


class AppleBooksError(ApplicationError):
    def __init__(self, message):
        super().__init__(message)
