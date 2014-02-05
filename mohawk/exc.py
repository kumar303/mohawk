
class HawkFail(Exception):
    pass


class InvalidConfig(HawkFail):
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


class ConfigLookupError(HawkFail):
    pass
