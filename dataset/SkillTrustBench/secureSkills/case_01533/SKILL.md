---
name: bp-reporting-templates
description: Generate BP monthly/quarterly/half-year/year report filling templates from BP data (API first, file fallback) with strict reviewer checks for code anchors, numeric traceability, and alert rules.
---

# bp-reporting-templates

## Mandatory pre-check (before generation)
When this skill is used, **always do two selections first**:
1. List and select BP period
2. List and select template types (月报/季报/半年报/年报/四套)

Do not generate until both are confirmed.

## Script entry
- `scripts/main.py`

## Useful commands
```bash
# 1) 列出可选周期（供用户选择）
python3 scripts/main.py --list-periods --app-key "$BP_APP_KEY"

# 2) 列出可选生成类型（供用户选择）
python3 scripts/main.py --list-template-types

# 3) 执行生成（示例：季报+年报）
python3 scripts/main.py "为产品中心生成" \
  --app-key "$BP_APP_KEY" \
  --period-id "<period_id>" \
  --template-types "季报,年报" \
  --output ./output

# 4) 输入中未识别组织时可显式指定
python3 scripts/main.py "生成季报" \
  --app-key "$BP_APP_KEY" \
  --period-id "<period_id>" \
  --org-name "产品中心" \
  --template-types "季报"
```

## Runtime rules
- `app_key` must come from env/arg (`BP_APP_KEY` or `COMPANY_APP_KEY`), not hardcoded in code.
- Team default: use the validated standard company key via env injection (prefer `BP_APP_KEY`).
- If period is missing and multiple periods exist, ask user to choose.
- If template types are missing, ask user to choose.
- Keep output markdown traceable to BP source content.
