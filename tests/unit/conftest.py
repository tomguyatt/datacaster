import logging
import sys

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s %(module)s.%(funcName)s:%(lineno)d %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)
