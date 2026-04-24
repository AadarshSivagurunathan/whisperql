import logging
import psycopg2

logger = logging.getLogger(__name__)

def get_connection(database_url: str = None):
    """Get a psycopg2 connection using the provided database URL."""
    try:
        if not database_url:
            logger.error("get_connection called with no database_url")
            raise ValueError("No database URL provided")
        logger.info("Attempting database connection to host (URL hidden for security)")
        conn = psycopg2.connect(database_url)
        logger.info("Database connection established successfully")
        return conn
    except psycopg2.OperationalError as e:
        logger.error("Database connection failed (OperationalError): %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error in get_connection: %s", e, exc_info=True)
        raise

def get_schema(conn: psycopg2.extensions.connection) -> str:
    """Introspect the connected PostgreSQL database and return a human-readable schema string for the public schema."""
    try:
        logger.info("Introspecting database schema for public tables")
        query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            logger.warning("No tables found in the public schema")
            return "No Tables found in the public Schema!"
        
        schema_dict = {}
        for table_name, column_name, data_type in rows:
            if table_name not in schema_dict:
                schema_dict[table_name] = []
            schema_dict[table_name].append((column_name, data_type))
            
        schema_str_lines = []
        for table, columns in schema_dict.items():
            quoted_table = f'"{table}"' if table != table.lower() else table
            schema_str_lines.append(f"Table: {quoted_table}")
            for col_name, data_type in columns:
                quoted_col = f'"{col_name}"' if col_name != col_name.lower() else col_name
                schema_str_lines.append(f"  - {quoted_col} ({data_type})")

        table_count = len(schema_dict)
        column_count = sum(len(cols) for cols in schema_dict.values())
        logger.info("Schema introspection complete: %d tables, %d columns", table_count, column_count)
        return "\n".join(schema_str_lines)
    except Exception as e:
        logger.error("Failed to introspect schema: %s", e, exc_info=True)
        raise

def execute_query(conn, sql: str) -> dict:
    """Execute the given SQL query safely, returning columns and rows on success, or an error message on failure."""
    try:
        logger.info("Executing SQL query: %s", sql[:200])
        cursor = conn.cursor()
        cursor.execute(sql)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            # Convert list of tuples to list of lists to be JSON serializable nicely in FastAPI
            rows = [list(r) for r in rows]
        else:
            conn.commit()
            columns = []
            rows = []
            
        cursor.close()
        logger.info("Query executed successfully: %d rows, %d columns returned", len(rows), len(columns))
        return {"columns": columns, "rows": rows, "error": None}
    except Exception as e:
        logger.error("Query execution failed: %s | SQL: %s", e, sql[:200], exc_info=True)
        try:
            conn.rollback()
            logger.info("Transaction rolled back successfully")
        except Exception as rb_err:
            logger.error("Rollback also failed: %s", rb_err, exc_info=True)
        return {"columns": [], "rows": [], "error": str(e)}
