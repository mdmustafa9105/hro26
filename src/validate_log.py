"""
Validator for log.txt conforming strictly to AGENTS.md Section 5 requirements.
"""

import os
import re
import sys

def validate_log(log_path="log.txt"):
    if not os.path.exists(log_path):
        print(f"FAIL: {log_path} does not exist.")
        return False

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    entries = re.split(r'\n(?=## \[)', content.strip())
    if not entries or not entries[0].startswith("## ["):
        print("FAIL: Log does not begin with a valid '## [TIMESTAMP]' header.")
        return False

    print(f"Auditing {len(entries)} entries in {log_path} against AGENTS.md Section 5...")

    errors = []
    session_starts = 0
    per_turn_entries = 0

    invalid_placeholders = {
        "<exact_harness_or_coding_agent_name>",
        "<exact_runtime_model_name>",
        "<absolute_path>",
        "<git_branch_or_unknown>",
        "<worktree_path_or_main>",
        "<parent_agent_name_or_none>",
        "<parent_name_or_none>",
        "unknown",
        "AI"
    }

    for idx, raw_entry in enumerate(entries):
        entry = raw_entry.strip()
        lines = [l.strip() for l in entry.splitlines() if l.strip()]
        if not lines:
            continue

        header = lines[0]
        m = re.match(r'^## \[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\]\s+(.+)$', header)
        if not m:
            errors.append(f"Entry {idx+1}: Header does not match '## [ISO-8601 TIMESTAMP] <title>': {header}")
            continue

        timestamp, title = m.group(1), m.group(2)

        if title == "SESSION START":
            session_starts += 1
            # Check mandatory fields
            req_keys = ["tool=", "model=", "Repo Root:", "Branch:", "Worktree:", "Parent Agent:"]
            for rk in req_keys:
                found = False
                for l in lines:
                    if l.startswith(rk):
                        val = l[len(rk):].strip()
                        if not val or val in invalid_placeholders:
                            errors.append(f"Entry {idx+1} (SESSION START): {rk} has invalid or placeholder value '{val}'")
                        found = True
                        break
                if not found:
                    errors.append(f"Entry {idx+1} (SESSION START): Missing required field '{rk}'")
        else:
            per_turn_entries += 1
            if len(title) > 80:
                errors.append(f"Entry {idx+1}: Title exceeds 80 characters ({len(title)} chars): '{title}'")

            # Check sections
            required_sections = [
                "User Prompt (verbatim, secrets redacted):",
                "Agent Response Summary:",
                "Actions:",
                "Context:"
            ]
            for sec in required_sections:
                if sec not in entry:
                    errors.append(f"Entry {idx+1}: Missing section '{sec}'")

            # Check Context fields
            context_keys = ["tool=", "model=", "branch=", "repo_root=", "worktree=", "parent_agent="]
            for ck in context_keys:
                found = False
                for l in lines:
                    if l.startswith(ck):
                        val = l[len(ck):].strip()
                        if not val or val in invalid_placeholders:
                            errors.append(f"Entry {idx+1}: Context field '{ck}' has invalid or placeholder value '{val}'")
                        found = True
                        break
                if not found:
                    errors.append(f"Entry {idx+1}: Missing Context field '{ck}'")

    if errors:
        print(f"VALIDATION FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return False

    print(f"VALIDATION PASSED: {len(entries)} entries ({session_starts} session starts, {per_turn_entries} per-turn entries) strictly conform to AGENTS.md Section 5.")
    return True

if __name__ == "__main__":
    success = validate_log()
    sys.exit(0 if success else 1)
