import logging
from logging.handlers import RotatingFileHandler

from .book import CondecoBooker


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        RotatingFileHandler('./logs.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler(),
    ],
)
