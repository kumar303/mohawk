
class HawkFail(Exception):
    pass


class InvalidCredentials(HawkFail):
    pass


class MacMismatch(HawkFail):
    pass


class DataTamperedWith(HawkFail):
    pass


class TokenExpired(HawkFail):

    def __init__(self, *args, **kw):
        self.localtime_in_seconds = kw.pop('localtime_in_seconds')
        super(HawkFail, self).__init__(*args, **kw)


class AlreadyProcessed(HawkFail):
    pass


class MisComputedContentHash(HawkFail):
    pass


class BadHeaderValue(HawkFail):
    pass


class CredentialsLookupError(HawkFail):
    pass
