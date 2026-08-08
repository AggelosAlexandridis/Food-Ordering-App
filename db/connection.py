import os

import mariadb
from dotenv import load_dotenv

load_dotenv()


def create_connection():
    # autocommit=True is required so this connection's reads always see rows
    # committed by *other* connections (e.g. a chef's app polling for orders
    # placed from a separate client process). MariaDB's Python connector
    # defaults to autocommit=False, which pins each connection to the
    # snapshot from its first query under REPEATABLE READ - it would never
    # observe new data until it happened to commit something itself.
    return mariadb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DATABASE"),
        autocommit=True,
    )
