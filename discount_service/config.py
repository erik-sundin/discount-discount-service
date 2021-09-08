import os


class Config():
    """
    Configuration object, passed to all routes and modules.
    """
    DEFAULT_DB_URL = "postgresql+asyncpg://postgresql:verysecret/postgres"

    def __init__(self):
        self.db_url = os.environ.get("DB_URL") or Config.DEFAULT_DB_URL
        self.logger = "Discount service"
