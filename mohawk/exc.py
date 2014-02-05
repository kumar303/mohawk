
class HawkFail(Exception):
    pass


class InvalidCredentials(HawkFail):
    pass


class MacMismatch(HawkFail):
    pass


class DataTamperedWith(HawkFail):
    pass


class TokenExpired(HawkFail):
    pass


class AlreadyProcessed(HawkFail):
    pass


class MisComputedContentHash(HawkFail):
    pass


class BadHeaderValue(HawkFail):
    pass


class CredentialsLookupError(HawkFail):
    pass
