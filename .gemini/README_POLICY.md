# Policy for README.md Modifications

This policy governs all changes to the `README.md` file. It is based on the principle that `SPEC.md` is the single source of truth.

1.  **High-Level Summary Only:** The `README.md` must remain a high-level, conceptual summary for end-users. It should explain the project's purpose and general setup, but nothing more.

2.  **No Implementation Details:** The `README.md` **must not** contain implementation details. This includes:
    -   Specific secret names (`GH_PAT`, `TELEGRAM_TOKEN`).
    -   Configuration file names (`repos.txt`).
    -   Specific values (e.g., issue limits, truncation lengths, schedule times).
    -   Detailed output examples that mirror the spec's template.

3.  **Defer to `SPEC.md`:** All sections discussing configuration, setup, or behavior must immediately and clearly defer to `SPEC.md` for specifics. The `README.md` should always end with a link to `SPEC.md` as the source of truth.

**Objective:** Prevent duplication and maintain `SPEC.md` as the authoritative document. Before making any changes to `README.md`, review this policy and the contents of `SPEC.md`.
