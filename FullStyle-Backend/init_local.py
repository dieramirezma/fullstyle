"""Explicit versioned initialization of the isolated synthetic database."""

from config.db_config import db
from config.server_config import create_app
from migrate_local import upgrade

if __name__ == "__main__":
    with create_app().app_context():
        versions = upgrade(db.engine)
    print("Synthetic schema ready at " + versions[-1])
