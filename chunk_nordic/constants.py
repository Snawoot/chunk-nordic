import enum
import logging


# pylint: disable=invalid-name
class LogLevel(enum.IntEnum):
    debug = logging.DEBUG
    info = logging.INFO
    warn = logging.WARN
    error = logging.ERROR
    fatal = logging.FATAL
    crit = logging.CRITICAL

    # pylint: disable=invalid-str-returned
    def __str__(self):
        return self.name


class Way(enum.Enum):
    upstream = 1
    downstream = 2


SERVER = "nginx"
BUFSIZE = 16 * 1024
