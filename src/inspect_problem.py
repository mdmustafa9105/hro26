with open("problem_statement.md", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if any(w in line.lower() for w in ["analytic", "anonymiz", "tombstone", "correlat"]):
            print(f"{i}: {line.strip()[:140]}")
