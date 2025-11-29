import logging
from .config import LOG_PATH

logger = logging.getLogger("pmcli")
logger.setLevel(logging.INFO)

fh = logging.FileHandler(LOG_PATH)
fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s] event=%(message)s"
)
fh.setFormatter(fmt)
logger.addHandler(fh)
