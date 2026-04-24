"""Tests for app/llm.py — generate_sql function."""

from unittest.mock import MagicMock, patch

from backend.app.llm import generate_sql


@patch("backend.app.llm.call_llm")
def test_generate_sql_basic(mock_call):
    """Verify generate_sql returns a non-empty string without markdown backticks."""
    mock_call.return_value = "SELECT * FROM users;"

    result = generate_sql("Table: users\n  - id (integer)", "Show all users")

    assert result
    assert "```" not in result
    assert result == "SELECT * FROM users;"


@patch("backend.app.llm.call_llm")
def test_generate_sql_strips_markdown(mock_call):
    """Verify markdown fences are stripped from the LLM response."""
    mock_call.return_value = "```sql\nSELECT 1\n```"

    result = generate_sql("Table: t\n  - id (integer)", "Give me 1")

    assert result == "SELECT 1"
    assert "```" not in result


@patch("backend.app.llm.call_llm")
def test_generate_sql_with_error_context(mock_call):
    """Verify the user message includes error context when previous_sql and error are given."""
    mock_call.return_value = "SELECT id FROM users;"

    generate_sql(
        schema="Table: users\n  - id (integer)",
        question="Show all user ids",
        previous_sql="SELECT ids FROM users;",
        error='column "ids" does not exist',
    )

    # Inspect the user_message argument passed to call_llm
    call_args = mock_call.call_args
    user_message = call_args[0][1]  # second positional arg
    assert "fix" in user_message.lower() or "failed" in user_message.lower()
    assert "ids" in user_message