import os
import re
import logging
import time
from google import genai
from openai import OpenAI
from google.genai import types
from anthropic import Anthropic
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

#Read provider from env -- supported values: "google", "anthropic", "openai"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "google").lower()
logger.info("LLM provider configured: %s", LLM_PROVIDER)

SYSTEM_PROMPT = (
    "You are a PostgreSQL Expert. Given the database schema below, "
    "write a SQL query that answers the user's question. \n\n"
    "IMPORTANT: If a table or column name appears in double quotes in the schema "
    "(e.g. \"Employee_details\"), you MUST use double quotes around it in your SQL query. "
    "PostgreSQL is case-sensitive for quoted identifiers.\n\n"
    "Return ONLY the raw SQL query. No explanation. No markdown. No backticks.\n\n"
    "Schema:\n{schema}"
)

def retry_on_error(max_retries=3, delay=1, backoff=2):
    """Retry decorator with exponential backoff for transient LLM API failures."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    if attempt < max_retries:
                        logger.warning(
                            "LLM call failed (attempt %d/%d): %s. Retrying in %ds...",
                            attempt, max_retries, exc, current_delay,
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "LLM call failed after all %d attempts: %s",
                            max_retries, exc, exc_info=True,
                        )
            raise last_exception
        return wrapper
    return decorator

def build_user_message(question: str, previous_sql: str = None, error: str = None) -> str:
    """Build the user message, optionally including error context for retry."""
    try:
        if previous_sql and error:
            msg = (
                f"{question}\n\n"
                f"The previous query was: {previous_sql}\n"
                f"It failed with: {error}\n"
                f"Please fix it"
            )
            logger.info("Built user message with error context for retry")
            return msg
        logger.debug("Built simple user message: %s", question[:100])
        return question
    except Exception as e:
        logger.error("Failed to build user message: %s", e, exc_info=True)
        raise


@retry_on_error(max_retries=3, delay=1, backoff=2)
def call_llm(system_message: str, user_message: str) -> str:
    """Call the configured LLM provider and return model's reply."""
    try:
        logger.info("Calling LLM provider: %s", LLM_PROVIDER)

        if LLM_PROVIDER == "google":
            API_KEY = os.getenv("GOOGLE_API_KEY")
            if not API_KEY:
                logger.error("GOOGLE_API_KEY is not set in environment")
                raise ValueError("GOOGLE_API_KEY is not set")
            client = genai.Client(api_key=API_KEY)

            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_message,
                ),
            )
            result = response.text.strip()

        elif LLM_PROVIDER == "anthropic":
            API_KEY = os.getenv("ANTHROPIC_API_KEY")
            if not API_KEY:
                logger.error("ANTHROPIC_API_KEY is not set in environment")
                raise ValueError("ANTHROPIC_API_KEY is not set")
            client = Anthropic(api_key=API_KEY)

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=system_message,
                messages=[{"role": "user", "content": user_message}],
                temperature=0,
            )
            result = response.content[0].text.strip()

        else:
            API_KEY = os.getenv("OPENAI_API_KEY")
            if not API_KEY:
                logger.error("OPENAI_API_KEY is not set in environment")
                raise ValueError("OPENAI_API_KEY is not set")
            client = OpenAI(api_key=API_KEY)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0,
            )
            result = response.choices[0].message.content.strip()

        logger.info("LLM response received (%d characters)", len(result))
        logger.debug("LLM raw response: %s", result[:300])
        return result

    except Exception as e:
        logger.error("LLM call to %s failed: %s", LLM_PROVIDER, e, exc_info=True)
        raise

def strip_markdown_fences(text: str) -> str:
    """Remove accidental markdown code fences from LLM output."""
    try:
        cleaned = re.sub(r"^```(?:sql)?\s*\n", "", text.strip())
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
        result = cleaned.strip()
        if result != text.strip():
            logger.info("Stripped markdown fences from LLM output")
        return result
    except Exception as e:
        logger.error("Failed to strip markdown fences: %s", e, exc_info=True)
        return text


def generate_sql(schema: str, question: str, previous_sql: str = None, error: str = None) -> str:
    """Generate or fix a SQL query using the configured LLM based on user question and database schema."""
    try:
        logger.info("Generating SQL for question: %s", question[:150])
        system_message = SYSTEM_PROMPT.format(schema=schema)
        user_message = build_user_message(question, previous_sql, error)
        raw = call_llm(system_message, user_message)
        sql = strip_markdown_fences(raw)
        logger.info("Generated SQL: %s", sql[:200])
        return sql
    except Exception as e:
        logger.error("generate_sql failed: %s", e, exc_info=True)
        raise