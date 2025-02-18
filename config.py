import os


def _require(name):
    """Return environment variable `name`, or fail loudly if it is missing.

    Secrets are never hardcoded in this file. A missing variable is a
    deployment error, so raise rather than fall back to a placeholder.
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            "Required environment variable {0} is not set. "
            "Copy .env.example to .env and provide a value for {0}.".format(name)
        )
    return value


class Config:
    SECRET_KEY = _require('SECRET_KEY')
    MONGO_URI = _require('MONGO_URI')
