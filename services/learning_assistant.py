"""Rule-based learning assistant. NOT an AI: it matches MySQL error numbers and common
mistake patterns to prewritten explanations."""
import difflib
import re

ERRORS = {
    1064: ("Syntax error", "MySQL could not understand the shape of your statement.",
           "Check keyword spelling, commas between columns, quotes around text, and matching parentheses. The text after 'near' in the message shows where MySQL got lost."),
    1146: ("Table does not exist", "The table name is wrong, or the table is not in the current sandbox scenario.",
           "Look at the table list in the schema panel (or DATABASE EXPLORER) and copy the name exactly."),
    1054: ("Unknown column", "A column name does not exist in that table.",
           "Compare with the schema panel. If you used text values, put them in single quotes: city = 'Cebu', not city = Cebu."),
    1052: ("Ambiguous column", "Two tables in your JOIN both have that column.",
           "Prefix the column with the table or alias: s.student_id instead of student_id."),
    1062: ("Duplicate entry", "A PRIMARY KEY or UNIQUE column already contains that value.",
           "Use a different value, or omit the AUTO_INCREMENT id and let MySQL choose it."),
    1048: ("Column cannot be NULL", "You tried to store nothing in a NOT NULL column.", "Provide a value for that column in your INSERT."),
    1136: ("Column count mismatch", "The number of values does not match the number of columns.", "Count the columns in parentheses and the values; they must be equal."),
    1452: ("Foreign key check failed", "The referenced parent row does not exist.", "Insert the parent row first (e.g. the student) or use an existing id."),
    1451: ("Row is referenced", "Other rows still point to this row through a foreign key.", "Delete or update the child rows first (e.g. enrollments), then the parent."),
    1055: ("GROUP BY problem", "A selected column is neither aggregated nor listed in GROUP BY.", "Add the column to GROUP BY or wrap it in MIN()/MAX()/COUNT()."),
    1111: ("Invalid use of aggregate", "Aggregates such as COUNT() cannot be used inside WHERE.", "Filter groups with HAVING instead of WHERE."),
    1366: ("Wrong value type", "The value does not fit the column's data type.", "Use numbers without quotes for INT columns and quoted text for VARCHAR."),
    1049: ("Unknown database", "The database does not exist.", "You never need to select a database here; the sandbox is already selected."),
    1142: ("Permission denied", "The sandbox account is not allowed to do that.", "This is intentional: the sandbox protects your other databases."),
    3024: ("Query timed out", "The query ran longer than the safety limit.", "Add a WHERE or LIMIT, and check for a JOIN missing its ON condition."),
}
KEYWORDS = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "WITH", "SHOW", "DESCRIBE", "START", "COMMIT", "ROLLBACK", "CALL", "TRUNCATE"]


def explain_error(errno, message, sql=""):
    base = ERRORS.get(errno)
    out = {"title": base[0] if base else "MySQL error", "meaning": base[1] if base else message,
           "fix": base[2] if base else "Read the message carefully; it names the problem and where it was found."}
    tips = heuristics(sql)
    if tips:
        out["likely"] = tips
    return out


def heuristics(sql):
    """Spot common beginner mistakes by pattern."""
    tips, s = [], (sql or "")
    low = s.lower()
    first = re.match(r"\s*(\w+)", s)
    if first and first.group(1).upper() not in KEYWORDS:
        guess = difflib.get_close_matches(first.group(1).upper(), KEYWORDS, n=1, cutoff=0.6)
        if guess:
            tips.append(f"'{first.group(1)}' looks like a typo of {guess[0]}.")
    if s.count("'") % 2:
        tips.append("You have an odd number of single quotes: one string is never closed.")
    if s.count("(") != s.count(")"):
        tips.append("Your parentheses are not balanced.")
    if re.search(r"[=<>!]\s*null\b", low) and not re.search(r"\bis\s+(not\s+)?null\b", low):
        tips.append("Use IS NULL / IS NOT NULL. Comparing with = NULL never matches anything.")
    if re.search(r"(=|like)\s*[a-z_]+\s*(;|$|\s+(and|or|order|group|limit)\b)", low) and not re.search(r"=\s*(null|true|false)\b", low):
        tips.append("Text values need single quotes, e.g. city = 'Cebu'.")
    if re.search(r",\s*from\b", low):
        tips.append("There is a comma right before FROM. Remove the last comma in the column list.")
    if re.match(r"\s*select\b", low) and "from" not in low and not re.search(r"select\s+[\d'(]", low):
        tips.append("A SELECT that reads a table needs a FROM clause.")
    if re.search(r"\b(count|sum|avg|min|max)\s*\(", low) and re.search(r"select\s+\w+\s*,", low) and "group by" not in low:
        tips.append("You mix a plain column with an aggregate function. Add GROUP BY for that column.")
    if re.search(r"\bwhere\b.*\b(count|sum|avg)\s*\(", low):
        tips.append("Aggregate functions cannot be used in WHERE. Use HAVING after GROUP BY.")
    if re.search(r"\bjoin\b", low) and not re.search(r"\b(on|using)\b|cross\s+join", low):
        tips.append("A JOIN needs an ON condition, e.g. ON s.student_id = e.student_id.")
    return tips


def why_wrong(sql, error=None, feedback=None):
    """Answer for the 'WHY IS THIS WRONG?' button."""
    msgs = []
    if error:
        e = explain_error(error.get("errno"), error.get("message", ""), sql)
        msgs += [f"{e['title']}: {e['meaning']}", "How to fix: " + e["fix"]] + e.get("likely", [])
    else:
        msgs += heuristics(sql)
        if feedback:
            msgs.append("Checker said: " + feedback)
        if not msgs:
            msgs.append("I found no common mistake pattern. Run your query and compare the output with the task, one clause at a time: FROM first, then WHERE, then the selected columns.")
    return msgs
