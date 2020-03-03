class InvalidDefaultValue(TypeError):
    pass


class UnexpectedArgument(ValueError):
    pass


class MissingArgument(ValueError):
    pass


class UnsupportedCast(ValueError):
    pass


class CastFailed(ValueError):
    pass


class MultipleCastDefinitions(Exception):
    pass
