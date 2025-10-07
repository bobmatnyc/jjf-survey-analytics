#!/usr/bin/env python3
"""
Database Utilities
Provides unified database connection handling for both SQLite and PostgreSQL.
"""

import os
import sqlite3
import re
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

# Detect database type from environment
DATABASE_URL = os.getenv('DATABASE_URL')
USE_POSTGRESQL = DATABASE_URL is not None


class DatabaseConnection:
    """
    Unified database connection handler.

    Automatically uses PostgreSQL when DATABASE_URL is set,
    otherwise falls back to SQLite.
    """

    def __init__(self, sqlite_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            sqlite_path: Path to SQLite database (ignored if DATABASE_URL is set)
        """
        self.use_postgresql = USE_POSTGRESQL
        self.database_url = DATABASE_URL
        self.sqlite_path = sqlite_path

        if self.use_postgresql:
            logger.info(f"Using PostgreSQL database")
            try:
                import psycopg2
            except ImportError:
                logger.error("psycopg2 not available for PostgreSQL")
                raise ImportError("psycopg2 required for PostgreSQL support")
        else:
            logger.info(f"Using SQLite database: {sqlite_path}")

    def get_connection(self):
        """
        Get database connection.

        Returns:
            Database connection object (psycopg2 or sqlite3)
        """
        if self.use_postgresql:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(self.database_url)
            # Use RealDictCursor for dict-like row access
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            return conn
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn

    def execute_query(self, query: str, params: tuple = None, fetch: str = None):
        """
        Execute a query with automatic connection handling.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: 'one', 'all', or None

        Returns:
            Query result based on fetch parameter
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'all':
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount


def adapt_sql_for_postgresql(sql: str) -> str:
    """
    Adapt SQLite SQL syntax to PostgreSQL.

    Args:
        sql: SQLite SQL statement

    Returns:
        PostgreSQL-compatible SQL statement
    """
    if not USE_POSTGRESQL:
        return sql

    # Log original SQL for debugging
    logger.debug(f"Adapting SQL: {sql[:100]}...")

    # Replace AUTOINCREMENT with SERIAL (handle all variations)
    sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
    sql = sql.replace('INTEGER AUTOINCREMENT PRIMARY KEY', 'SERIAL PRIMARY KEY')

    # Replace standalone AUTOINCREMENT in column definitions
    # Match pattern: column_name INTEGER AUTOINCREMENT
    import re
    sql = re.sub(r'(\w+\s+)INTEGER\s+AUTOINCREMENT', r'\1SERIAL', sql, flags=re.IGNORECASE)

    # Replace DATETIME with TIMESTAMP
    sql = sql.replace('DATETIME', 'TIMESTAMP')

    # Replace BOOLEAN 0/1 with TRUE/FALSE
    sql = sql.replace('BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE')
    sql = sql.replace('BOOLEAN DEFAULT 1', 'BOOLEAN DEFAULT TRUE')

    # Replace DEFAULT CURRENT_TIMESTAMP (SQLite) with DEFAULT CURRENT_TIMESTAMP (PostgreSQL is same)
    # But handle datetime('now') which is SQLite-specific
    sql = sql.replace("datetime('now')", "CURRENT_TIMESTAMP")
    sql = sql.replace("DATETIME('now')", "CURRENT_TIMESTAMP")

    # Replace INSERT OR IGNORE with INSERT ... ON CONFLICT DO NOTHING
    if 'INSERT OR IGNORE INTO' in sql:
        # Extract table name and columns
        match = re.search(r'INSERT OR IGNORE INTO\s+(\w+)\s*\(([^)]+)\)', sql, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            # For ON CONFLICT, we need to know the unique constraint
            # For now, use DO NOTHING which works without specifying constraint
            sql = sql.replace('INSERT OR IGNORE INTO', 'INSERT INTO')
            # Add ON CONFLICT DO NOTHING at the end before any RETURNING clause
            if 'RETURNING' in sql:
                sql = sql.replace(' RETURNING', ' ON CONFLICT DO NOTHING RETURNING')
            else:
                sql = sql.rstrip(';').rstrip() + ' ON CONFLICT DO NOTHING'

    # Replace INSERT OR REPLACE with INSERT ... ON CONFLICT DO UPDATE
    if 'INSERT OR REPLACE INTO' in sql:
        # Extract table name
        match = re.search(r'INSERT OR REPLACE INTO\s+(\w+)\s*\(([^)]+)\)', sql, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            columns = [col.strip() for col in match.group(2).split(',')]

            # PostgreSQL requires explicit conflict target
            # We'll assume the first column or 'id' is the unique constraint
            conflict_column = 'id' if 'id' in columns else columns[0]

            # Build UPDATE clause for all columns except the conflict column
            update_columns = [col for col in columns if col != conflict_column]
            update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])

            sql = sql.replace('INSERT OR REPLACE INTO', 'INSERT INTO')

            if 'RETURNING' in sql:
                # Insert ON CONFLICT before RETURNING
                sql = sql.replace(' RETURNING',
                    f' ON CONFLICT ({conflict_column}) DO UPDATE SET {update_clause} RETURNING')
            else:
                sql = sql.rstrip(';').rstrip() + f' ON CONFLICT ({conflict_column}) DO UPDATE SET {update_clause}'

    # Log adapted SQL for debugging
    logger.debug(f"Adapted SQL: {sql[:100]}...")

    return sql


def get_placeholder(index: int = 0) -> str:
    """
    Get SQL parameter placeholder for current database.

    Args:
        index: Parameter index (for PostgreSQL positional parameters)

    Returns:
        '?' for SQLite, '%s' for PostgreSQL
    """
    if USE_POSTGRESQL:
        return '%s'
    else:
        return '?'


def get_last_insert_id(cursor) -> int:
    """
    Get last inserted ID in a database-agnostic way.

    Args:
        cursor: Database cursor

    Returns:
        Last inserted ID
    """
    if USE_POSTGRESQL:
        # PostgreSQL uses RETURNING clause or currval
        # This should be called after INSERT with RETURNING id
        return cursor.fetchone()[0] if cursor.rowcount > 0 else None
    else:
        # SQLite uses lastrowid
        return cursor.lastrowid


class DatabaseAdapter:
    """
    High-level database adapter for extractor and normalizer.

    Provides methods that work with both SQLite and PostgreSQL,
    handling schema differences automatically.
    """

    def __init__(self, db_path: str):
        """
        Initialize database adapter.

        Args:
            db_path: SQLite database path (ignored if DATABASE_URL is set)
        """
        self.db_connection = DatabaseConnection(db_path)

    def get_connection(self):
        """Get database connection."""
        return self.db_connection.get_connection()

    def execute_schema(self, schema_sql: str):
        """
        Execute schema creation SQL with automatic adaptation.

        Args:
            schema_sql: SQLite schema SQL
        """
        adapted_sql = adapt_sql_for_postgresql(schema_sql)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(adapted_sql)
            conn.commit()

    def insert_returning_id(self, table: str, columns: list, values: list) -> int:
        """
        Insert a row and return its ID.

        Args:
            table: Table name
            columns: Column names
            values: Column values

        Returns:
            Inserted row ID
        """
        placeholders = ', '.join([get_placeholder() for _ in values])
        columns_str = ', '.join(columns)

        if USE_POSTGRESQL:
            sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) RETURNING id"
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
                return cursor.fetchone()['id']
        else:
            sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
                return cursor.lastrowid


# Convenience functions for backward compatibility
def get_db_connection(db_path: str):
    """
    Get database connection (backward compatible).

    Args:
        db_path: SQLite database path

    Returns:
        Database connection
    """
    adapter = DatabaseConnection(db_path)
    return adapter.get_connection()


def is_postgresql() -> bool:
    """Check if using PostgreSQL."""
    return USE_POSTGRESQL


def is_sqlite() -> bool:
    """Check if using SQLite."""
    return not USE_POSTGRESQL
