"""Compatibility exports for the runtime application factory."""

from config.db_config import db as db
from config.runtime_config import create_app as create_app
from config.runtime_config import run_server as run_server
