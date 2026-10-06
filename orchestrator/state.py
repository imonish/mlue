from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):

    user_query: str

    route: str

    schema: str

    generated_sql: str

    sql_result: str

    error: Optional[str]

    retry_count: int

    final_answer: str