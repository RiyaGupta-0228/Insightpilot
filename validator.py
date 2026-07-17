import sqlite3
import re

def validate_sql(sql, db_path="retail.db"):
    """
    Checks AI-generated SQL before execution.
    Returns (True, "OK") if safe, or (False, reason) if rejected.
    """

    # Check 1: Must be a single statement (no sneaky "SELECT ...; DELETE ...")
    # Strip a single trailing semicolon first, then reject any remaining ones
    cleaned = sql.strip().rstrip(";")
    if ";" in cleaned:
        return False, "Multiple SQL statements are not allowed"

    # Check 2: Must start with SELECT (or WITH, for CTE queries)
    first_word = cleaned.split()[0].upper() if cleaned.split() else ""
    if first_word not in ("SELECT", "WITH"):
        return False, f"Only SELECT queries are allowed, got: {first_word}"

    # Check 3: Block dangerous keywords anywhere in the query
    forbidden = ["DELETE", "DROP", "UPDATE", "INSERT", "ALTER",
                 "CREATE", "TRUNCATE", "REPLACE", "ATTACH", "PRAGMA"]
    for word in forbidden:
        # \b = word boundary, so "CREATED_DATE" doesn't false-trigger on "CREATE"
        if re.search(rf"\b{word}\b", cleaned.upper()):
            return False, f"Forbidden keyword found: {word}"

    # Check 4: Does it actually parse and run? Use EXPLAIN - it compiles
    # the query without executing it, catching syntax errors and
    # non-existent tables/columns for free.
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(f"EXPLAIN {cleaned}")
        conn.close()
    except sqlite3.Error as e:
        return False, f"SQL error: {e}"

    return True, "OK"


# Test suite - run this file directly to check the validator works
if __name__ == "__main__":
    tests = [
        ("SELECT country FROM transactions LIMIT 5", True),
        ("DELETE FROM transactions WHERE country = 'France'", False),
        ("SELECT * FROM transactions; DROP TABLE transactions", False),
        ("SELECT nonexistent_column FROM transactions", False),
        ("SELECT * FROM fake_table", False),
        ("UPDATE transactions SET quantity = 0", False),
        ("SELECT invoice, quantity FROM transactions WHERE quantity > 0 LIMIT 3", True),
    ]

    for sql, expected_ok in tests:
        ok, reason = validate_sql(sql)
        status = "PASS" if ok == expected_ok else "FAIL"
        print(f"[{status}] {'allowed' if ok else 'blocked':7} | {reason:40} | {sql[:50]}")
