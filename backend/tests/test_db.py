"""Tests for app/db.py — execute_query function."""

from unittest.mock import MagicMock, patch

from backend.app.db import execute_query


def test_execute_query_success():
    """Verify execute_query returns correct columns and rows on success."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Simulate a successful query with two columns and two rows
    mock_cursor.description = [("id",), ("name",)]
    mock_cursor.fetchall.return_value = [(1, "Alice"), (2, "Bob")]

    result = execute_query(mock_conn, "SELECT id, name FROM users;")

    assert result["error"] is None
    assert result["columns"] == ["id", "name"]
    assert result["rows"] == [[1, "Alice"], [2, "Bob"]]
    mock_cursor.execute.assert_called_once_with("SELECT id, name FROM users;")


def test_execute_query_error():
    """Verify execute_query returns an error message when the query fails."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Simulate a database error
    mock_cursor.execute.side_effect = Exception("relation \"bad_table\" does not exist")

    result = execute_query(mock_conn, "SELECT * FROM bad_table;")

    assert result["error"] is not None
    assert "bad_table" in result["error"]
    assert result["columns"] == []
    assert result["rows"] == []
    mock_conn.rollback.assert_called_once()