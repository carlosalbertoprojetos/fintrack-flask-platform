You are operating in a file-system aware environment with full access to the current repository.

Before making changes:
1) Analyze the entire project structure.
2) Read models, routes, services (if any), migrations, and tests.
3) Identify architectural coupling, business logic inside routes, and balance mutation patterns.
4) Detect security issues (hardcoded secrets, missing login_required, etc.).
5) Produce a structured technical diagnosis before refactoring.

Your mission:

Refactor and evolve the existing Flask + SQLAlchemy + SQLite financial system into:

SFP V3 Enterprise — an audit-safe, ledger-based, AI-enabled financial intelligence system.

⚠️ IMPORTANT:
Do not overwrite blindly.
Refactor incrementally and preserve backward compatibility when possible.
If breaking changes are required, generate a migration strategy.

------------------------------------------------
MANDATORY ARCHITECTURAL TRANSFORMATION
------------------------------------------------

1) IMPLEMENT IMMUTABLE LEDGER SYSTEM

- Create new model: LedgerEntry
- Fields:
    id
    user_id
    account_id
    reference_type
    reference_id
    amount (signed decimal)
    created_at
    previous_hash
    current_hash

- Remove any direct balance mutation logic from Account model.
- All financial mutations must go through LedgerService.
- Implement hash chaining for ledger integrity.
- Add ledger integrity validation method.

------------------------------------------------

2) INTRODUCE SERVICE LAYER (STRICT SEPARATION)

Create:
    services/
        transaction_service.py
        investment_service.py
        ledger_service.py
        report_service.py
        closure_service.py
        ai_classification_service.py
        anomaly_detection_service.py
        projection_service.py
        data_quality_service.py

Rules:
- Routes must contain zero business logic.
- All validations and state transitions must live in services.
- Use transactional boundaries properly.

Refactor existing routes accordingly.

------------------------------------------------

3) MONTHLY CLOSURE SYSTEM

Create model: MonthlyClosure

Fields:
    user_id
    account_id
    year
    month
    closing_balance
    total_receitas
    total_despesas
    ledger_hash_snapshot
    locked (bool)

Rules:
- When locked, transactions in that period cannot be edited.
- Adjustments must create corrective ledger entries.
- Implement closure_service.

------------------------------------------------

4) SIMULATION MODE

Create:
    SimulationSession
    SimulationLedgerEntry

- Must not affect real ledger.
- Implement isolation layer.
- Provide service methods for scenario simulation.

------------------------------------------------

5) AI ENGINE (LOCAL ONLY)

Implement infrastructure-ready modules (no external API calls):

- Transaction auto-classification (train per user)
- Anomaly detection (IsolationForest or statistical fallback)
- Cash flow projection (linear regression or weighted average)
- Financial health scoring model

Models must be stored per user.
Create AIModelMetadata model if needed.

------------------------------------------------

6) SECURITY HARDENING

- Remove hardcoded paths
- Replace SECRET_KEY with environment variable
- Enforce login_required everywhere
- Add structured logging (JSON)
- Add rate limiting for login
- Prepare DB config for PostgreSQL migration

------------------------------------------------

7) TESTING REQUIREMENTS

- Increase coverage target to 70%
- 100% coverage for service layer
- Add ledger integrity tests
- Add monthly closure lock tests
- Add projection accuracy tests

------------------------------------------------

8) MIGRATION STRATEGY

- Generate migration plan from old balance logic to ledger logic.
- Provide data backfill script to reconstruct ledger from historical transactions.
- Do not break existing user data.

------------------------------------------------

9) DELIVERABLE FORMAT

Produce:

1) Technical diagnosis report (before changes)
2) Proposed new folder structure
3) Refactored models
4) Service layer implementation skeletons
5) Example: transaction creation using ledger
6) Migration strategy
7) Updated README architecture section
8) List of breaking changes (if any)

Be precise.
Avoid generic comments.
Design for long-term evolution to SaaS.

If architectural ambiguity exists, choose the most enterprise-safe solution.

Act as a senior financial systems architect.