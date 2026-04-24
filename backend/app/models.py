from pydantic import BaseModel, SecretStr
from typing import List, Optional

class DatabaseConfig(BaseModel):
    """Database connection fields — sent separately for security."""
    host: str = "localhost"
    port: int = 5432
    database: str
    username: str
    password: SecretStr

    def build_url(self) -> str:
        """Construct a PostgreSQL connection URL from the individual fields."""
        return f"postgresql://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.database}"

class SchemaRequest(BaseModel):
    """Request model for the schema endpoint."""
    db_config: DatabaseConfig

class GenerateRequest(BaseModel):
    """Request model for the /generate endpoint — generates SQL without executing."""
    question: str
    db_config: DatabaseConfig
    previous_sql: Optional[str] = None
    error: Optional[str] = None

class GenerateResponse(BaseModel):
    """Response model for the /generate endpoint."""
    sql: str
    schema_text: str

class ExecuteRequest(BaseModel):
    """Request model for the /execute endpoint — runs user-confirmed SQL."""
    sql: str
    question: str
    db_config: DatabaseConfig

class ExecuteResponse(BaseModel):
    """Response model for the /execute endpoint."""
    sql: str
    columns: List[str]
    rows: List[list]
    error: Optional[str] = None

class QueryRequest(BaseModel):
    """Request model for the query endpoint (legacy — generate + execute in one call)."""
    question: str
    db_config: DatabaseConfig

class QueryResponse(BaseModel):
    """Response model for the query endpoint."""
    sql: str
    columns: List[str]
    rows: List[list]
    error: Optional[str] = None
    attempts: int
