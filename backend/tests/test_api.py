"""Tests for app/main.py — FastAPI endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.app.main import app, query_history

client = TestClient(app)

# Reusable test db_config payload
TEST_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "testdb",
    "username": "user",
    "password": "pass",
}


def test_health_endpoint():
    """Verify GET /health returns 200 and the expected JSON."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("backend.app.main.db.get_schema")
@patch("backend.app.main.db.get_connection")
@patch("backend.app.main.llm.generate_sql")
def test_generate_endpoint(mock_gen, mock_conn, mock_schema):
    """Verify POST /generate returns SQL without executing it."""
    mock_connection = MagicMock()
    mock_conn.return_value = mock_connection
    mock_schema.return_value = "Table: users\n  - id (integer)"
    mock_gen.return_value = "SELECT id FROM users;"

    response = client.post(
        "/generate",
        json={
            "question": "Show all user ids",
            "db_config": TEST_DB_CONFIG,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sql"] == "SELECT id FROM users;"
    assert "schema_text" in data


@patch("backend.app.main.db.execute_query")
@patch("backend.app.main.db.get_connection")
def test_execute_endpoint(mock_conn, mock_exec):
    """Verify POST /execute runs user-confirmed SQL."""
    mock_connection = MagicMock()
    mock_conn.return_value = mock_connection
    mock_exec.return_value = {
        "columns": ["id"],
        "rows": [[1], [2], [3]],
        "error": None,
    }

    response = client.post(
        "/execute",
        json={
            "sql": "SELECT id FROM users;",
            "question": "Show all user ids",
            "db_config": TEST_DB_CONFIG,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sql"] == "SELECT id FROM users;"
    assert data["columns"] == ["id"]
    assert data["rows"] == [[1], [2], [3]]
    assert data["error"] is None


@patch("backend.app.main.db.execute_query")
@patch("backend.app.main.llm.generate_sql")
@patch("backend.app.main.db.get_schema")
@patch("backend.app.main.db.get_connection")
def test_query_endpoint_success(mock_conn, mock_schema, mock_gen, mock_exec):
    """Verify POST /query (legacy) returns a valid QueryResponse on success."""
    mock_connection = MagicMock()
    mock_conn.return_value = mock_connection
    mock_schema.return_value = "Table: users\n  - id (integer)"
    mock_gen.return_value = "SELECT id FROM users;"
    mock_exec.return_value = {
        "columns": ["id"],
        "rows": [[1], [2], [3]],
        "error": None,
    }

    response = client.post(
        "/query",
        json={
            "question": "Show all user ids",
            "db_config": TEST_DB_CONFIG,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sql"] == "SELECT id FROM users;"
    assert data["columns"] == ["id"]
    assert data["rows"] == [[1], [2], [3]]
    assert data["error"] is None
    assert data["attempts"] == 1


def test_history_starts_empty():
    """Verify GET /history returns an empty list on a fresh app start."""
    # Clear any history from previous tests
    query_history.clear()
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == []