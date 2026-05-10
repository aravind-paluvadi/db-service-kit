"""
Initialization file for the PostgreSQL Database. This allows to mask the main file structure and allow importing the
class.

EXAMPLE:
    Instead of importing PostgresDBModule from db_modules, users can import it directly from db_modules. This promotes
cleaner and more convenient imports for users of the package.
"""
# db_modules/__init__.py
from .postgres_db_module import PostgresDBModule


__all__ = ['PostgresDBModule']