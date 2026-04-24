import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.models import (
    SchemaRequest,
    GenerateRequest, GenerateResponse,
    ExecuteRequest, ExecuteResponse,
    QueryRequest, QueryResponse,
)
from backend.app import db
from backend.app import llm

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Automated SQL Query Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory history list
query_history = []

MAX_RETRIES = 3


@app.get("/health")
def health_check():
    """Return an ok status for health checks."""
    try:
        logger.debug("Health check requested")
        return {"status": "ok"}
    except Exception as e:
        logger.error("Health check failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schema")
def get_schema_endpoint(request: SchemaRequest):
    """Return the database schema. Connection details are sent as separate secure fields."""
    try:
        logger.info("Schema request received for database: %s", request.db_config.database)
        database_url = request.db_config.build_url()
        logger.info("Connecting to database to fetch schema...")
        conn = db.get_connection(database_url)
        schema = db.get_schema(conn)
        conn.close()
        logger.info("Schema fetched and connection closed successfully")
        return {"schema": schema}
    except Exception as e:
        logger.error("Schema endpoint failed: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ── Step 1: Generate SQL only (no execution) ──────────────────────────────────
@app.post("/generate", response_model=GenerateResponse)
def generate_sql_endpoint(request: GenerateRequest):
    """Generate a SQL query from a natural language question without executing it."""
    try:
        logger.info("Generate request — question: %s", request.question[:150])
        database_url = request.db_config.build_url()
    except Exception as e:
        logger.error("Failed to build database URL: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid database config: {e}")

    try:
        conn = db.get_connection(database_url)
    except Exception as e:
        logger.error("Database connection failed: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=f"Database connection error: {e}")

    try:
        schema = db.get_schema(conn)
    except Exception as e:
        logger.error("Schema introspection failed: %s", e, exc_info=True)
        conn.close()
        raise HTTPException(status_code=400, detail=f"Failed to get schema: {e}")

    conn.close()

    try:
        sql = llm.generate_sql(
            schema, request.question,
            previous_sql=request.previous_sql,
            error=request.error,
        )
        logger.info("SQL generated successfully: %s", sql[:200])
        return GenerateResponse(sql=sql, schema_text=schema)
    except Exception as e:
        logger.error("LLM generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"LLM Error: {e}")


# ── Step 2: Execute user-confirmed SQL ────────────────────────────────────────
@app.post("/execute", response_model=ExecuteResponse)
def execute_sql_endpoint(request: ExecuteRequest):
    """Execute a user-confirmed SQL query against the database."""
    try:
        logger.info("Execute request — SQL: %s", request.sql[:200])
        database_url = request.db_config.build_url()
    except Exception as e:
        logger.error("Failed to build database URL: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid database config: {e}")

    try:
        conn = db.get_connection(database_url)
    except Exception as e:
        logger.error("Database connection failed: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=f"Database connection error: {e}")

    result = db.execute_query(conn, request.sql)
    conn.close()

    success = result["error"] is None
    history_item = {"question": request.question, "sql": request.sql, "success": success}
    query_history.append(history_item)
    if len(query_history) > 10:
        query_history.pop(0)

    if success:
        logger.info("Query executed successfully — %d rows returned", len(result["rows"]))
    else:
        logger.warning("Query execution failed: %s", result["error"])

    return ExecuteResponse(
        sql=request.sql,
        columns=result["columns"],
        rows=result["rows"],
        error=result["error"],
    )


# ── Legacy: Generate + Execute in one call (kept for backward compatibility) ──
@app.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    """Generate and run a SQL query, attempting up to 3 times on error."""
    try:
        logger.info("Query request received — question: %s", request.question[:150])
        database_url = request.db_config.build_url()
    except Exception as e:
        logger.error("Failed to build database URL: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid database config: {e}")

    try:
        conn = db.get_connection(database_url)
    except Exception as e:
        logger.error("Database connection failed: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=f"Database connection error: {e}")

    try:
        schema = db.get_schema(conn)
    except Exception as e:
        logger.error("Schema introspection failed: %s", e, exc_info=True)
        conn.close()
        raise HTTPException(status_code=400, detail=f"Failed to get schema: {e}")

    attempts = 0
    previous_sql = None
    error_msg = None
    sql = ""

    while attempts < MAX_RETRIES:
        attempts += 1
        logger.info("Query attempt %d/%d", attempts, MAX_RETRIES)

        try:
            sql = llm.generate_sql(schema, request.question, previous_sql=previous_sql, error=error_msg)
            logger.info("Attempt %d — generated SQL: %s", attempts, sql[:200])
        except Exception as e:
            error_msg = f"LLM Error: {e}"
            logger.error("Attempt %d — LLM generation failed: %s", attempts, e, exc_info=True)
            continue

        result = db.execute_query(conn, sql)
        if result["error"] is None:
            conn.close()
            logger.info("Query succeeded on attempt %d — %d rows returned", attempts, len(result["rows"]))

            history_item = {"question": request.question, "sql": sql, "success": True}
            query_history.append(history_item)
            if len(query_history) > 10:
                query_history.pop(0)

            return QueryResponse(
                sql=sql,
                columns=result["columns"],
                rows=result["rows"],
                error=None,
                attempts=min(attempts, MAX_RETRIES),
            )
        else:
            previous_sql = sql
            error_msg = result["error"]
            logger.warning("Attempt %d — SQL execution failed: %s", attempts, error_msg)

    conn.close()
    logger.error(
        "All %d attempts exhausted for question: %s | Last error: %s",
        MAX_RETRIES, request.question[:100], error_msg,
    )

    history_item = {"question": request.question, "sql": sql, "success": False}
    query_history.append(history_item)
    if len(query_history) > 10:
        query_history.pop(0)

    return QueryResponse(
        sql=sql,
        columns=[],
        rows=[],
        error=error_msg,
        attempts=attempts,
    )


@app.get("/history")
def get_history_endpoint():
    """Return the last 10 query history items."""
    try:
        logger.debug("History requested — %d items available", len(query_history))
        return query_history[-10:]
    except Exception as e:
        logger.error("History endpoint failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
