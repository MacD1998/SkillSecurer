---
name: bank-recon
description: Perform bank reconciliation between bank statement and general ledger Excel files. Supports custom thresholds for amount matching and semantic description matching. Use when the user wants to reconcile financial records, find matching transactions, and generate a reconciliation report in Excel.
---

# Bank Reconciliation Skill

This skill automates the process of matching bank statement records with general ledger entries.

## Workflow

1. **Input Verification**: Identify the paths to `bank_data.xlsx` and `gl_data.xlsx`.
2. **Threshold Configuration**: Ask the user for a reconciliation threshold (e.g., "Allow matches within $1.00?"). Default is $0.00.
3. **Execution**: Run the `scripts/recon_logic.py` script to process the files.
4. **Reporting**: Provide the resulting `recon_results.xlsx` file which details:
   - Matched records from both sides.
   - Match basis (Amount, Description, or both).
   - Variances within the threshold.

## Tool Usage

Run the reconciliation script using Python:

```bash
python3 scripts/recon_logic.py <bank_xlsx> <gl_xlsx> <output_xlsx> <threshold>
```

## Description Matching Logic
The skill uses semantic matching to identify common vendor names, invoice IDs, or transaction references between the bank description and GL memo.
