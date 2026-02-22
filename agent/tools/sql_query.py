"""
STREAM Agent Tool — SQL Query (Natural Language → SQL).

Accepts a natural language question about procurement data, converts it to
a read-only SQL query, executes against Neon PostgreSQL, and returns results.
"""

import re
from langchain_core.tools import tool
from agent.llm import get_llm
from agent.prompts import DB_SCHEMA_FOR_SQL, SQL_FEW_SHOTS
from db import fetch_all

# Dangerous SQL keywords that must never appear in generated queries
_WRITE_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|EXEC)\b",
    re.IGNORECASE,
)

MAX_ROWS = 50


def _build_nl2sql_prompt(question: str) -> str:
    """Build the prompt that turns a natural language question into SQL."""
    few_shot_text = "\n".join(
        f"Q: {ex['question']}\nSQL: {ex['sql']}\n" for ex in SQL_FEW_SHOTS
    )
    return f"""You are an expert SQL generator for a PostgreSQL database.
Given the schema below and the user's question, generate a single SELECT query.

{DB_SCHEMA_FOR_SQL}

## Examples
{few_shot_text}

## Rules
1. ONLY generate SELECT queries — never INSERT, UPDATE, DELETE, DROP, etc.
2. Always LIMIT results to {MAX_ROWS} rows unless the user asks for a specific count.
3. Use ILIKE for text searches (case-insensitive).
4. Monetary amounts are in INR. 1 crore = 10,000,000.
5. Return ONLY the SQL query, nothing else — no markdown, no explanation.

User question: {question}

SQL:"""


@tool
def query_database(question: str) -> str:
    """
    Query the STREAM procurement database using natural language.
    Use this tool when the auditor asks a data question — counts, listings,
    aggregations, filtering, or comparisons across tenders, companies,
    vendors, bonds, or entities.

    Args:
        question: The natural language question about the data.

    Returns:
        Formatted query results or an error message.
    """
    try:
        # Step 1: Generate SQL from question
        llm = get_llm(temperature=0)
        prompt = _build_nl2sql_prompt(question)
        response = llm.invoke(prompt)
        sql = response.content.strip()

        # Clean up markdown fences if present
        sql = re.sub(r"^```(?:sql)?\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)
        sql = sql.strip().rstrip(";")

        # Step 2: Validate — reject write operations
        if _WRITE_PATTERN.search(sql):
            return "ERROR: Generated query contains write operations. Only SELECT queries are allowed."

        if not sql.upper().startswith("SELECT"):
            return f"ERROR: Generated query does not start with SELECT: {sql[:100]}"

        # Step 3: Execute
        rows = fetch_all(sql)

        if not rows:
            return f"Query returned no results.\nSQL used: {sql}"

        # Step 4: Format output
        columns = list(rows[0].keys())
        header = " | ".join(columns)
        separator = " | ".join("-" * min(len(c), 20) for c in columns)

        result_lines = [header, separator]
        for row in rows[:MAX_ROWS]:
            values = []
            for col in columns:
                v = row.get(col)
                if v is None:
                    values.append("NULL")
                elif isinstance(v, float):
                    if abs(v) >= 1e7:
                        values.append(f"₹{v/1e7:.2f}Cr")
                    else:
                        values.append(f"{v:,.2f}")
                else:
                    values.append(str(v)[:60])
            result_lines.append(" | ".join(values))

        truncation = ""
        if len(rows) > MAX_ROWS:
            truncation = f"\n... ({len(rows)} total rows, showing first {MAX_ROWS})"

        return f"Results ({len(rows)} rows):\n\n" + "\n".join(result_lines) + truncation + f"\n\nSQL used: {sql}"

    except Exception as e:
        return f"ERROR executing query: {type(e).__name__}: {str(e)}"
