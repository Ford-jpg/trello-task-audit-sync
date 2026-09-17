def categorize_commit(msg: str) -> str:
    """
    Categorizes a commit message into one of the four MPOR audit categories:
    - Database Design
    - System Security
    - Bug Fix
    - System Module
    """
    m = msg.lower()

    # 1. System Database design created
    if any(k in m for k in ["database", "schema", "migration", "domain model", "erd", "model and migration"]):
        if not any(k in m for k in ["prevent destructive", "refreshdatabase"]):
            return "Database Design"

    # 2. System Security
    if any(k in m for k in ["security", "firewall", "fail2ban", "ssh key", "guardrail", "destructive command", "permission", "authorization", "rbac", "self-approval", "secret validation"]):
        return "System Security"

    # 3. Bug Fixes Performed
    if any(k in m for k in ["fix:", "fix(", "bug", "patch", "typo", "casing", "resolve type error", "refreshdatabase"]):
        return "Bug Fix"

    # 4. System Modules developed
    return "System Module"
