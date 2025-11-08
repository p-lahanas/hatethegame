import logging
from logging.handlers import RotatingFileHandler

from .condeco import CondecoBooker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        RotatingFileHandler('./logs/htg.log', maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler(),
    ],
)
