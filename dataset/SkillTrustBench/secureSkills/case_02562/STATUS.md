# sql-migration-linter — STATUS

**Status:** Built, tested, ready to publish.

- [ ] Published to ClawHub

**Price:** $59

**Category:** Database, migrations, code quality, linters

## Built
- [x] Script: `scripts/sql_migration_linter.py` (pure Python stdlib, ~400 lines)
- [x] SKILL.md with commands, rules, formats, exit codes, examples
- [x] 17 rules across 4 categories (structure, DDL safety, DML safety, transactions)
- [x] Dialect support: generic, postgres, mysql, sqlite
- [x] 3 output formats (text, json, summary)
- [x] CI-friendly exit codes (0/1/2) and --min-severity filter
- [x] Tested with clean and intentionally-broken migration files

## Market fit
- ZERO direct competition on ClawHub for sqlfluff-style SQL linting
- Closest hits are sql-toolkit, sql-formatter — formatters, not linters
- Broad backend audience (every project with a database)

## Next steps
- [ ] Publish (after today's session or next cron)
- [ ] Monitor for install/rating feedback
