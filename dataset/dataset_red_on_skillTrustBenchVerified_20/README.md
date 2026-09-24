# RED-generated 20-skill dataset

This directory contains the REDINJECTOR dataset used in Section 6.4. It is
constructed from 20 skills in `../skillTrustBenchVerified_20/`, with one
injected variant for each of nine threat types, for a total of 180 instances.

## Contents

- `injected/`: generated Markdown skills and `ground_truth.json`.
- `injected/ground_truth.json`: the expected injection text, vulnerability
  type, and difficulty for each generated filename.
- `red_injector_validation_prompt.md`: the model-independent validation prompt
  used to assess the generated dataset before scanner evaluation.

The nine threat types are `arbitrary_script_execution`,
`credential_exposure`, `data_exfiltration`, `guardfall`,
`indirect_injection`, `privilege_escalation`, `prompt_hijacking`,
`resource_exhaustion`, and `supply_chain`.

## Validation process

Use `red_injector_validation_prompt.md` with an independent frontier model.
The validation is static: do not execute commands, scripts, or URLs contained
in the generated skills.

For every skill--threat-type pair, the validation checks:

1. coverage of the requested 20 x 9 pairs;
2. uniqueness of the generated case and ground-truth entry;
3. presence of the recorded injection in the generated skill;
4. consistency between the injection and its `ground_truth.json` metadata; and
5. semantic alignment with the declared threat type.

The prompt additionally asks the reviewer to assess plausible placement,
formatting, and unintended modifications relative to the benign original when
that original is available. These checks validate the quality of the generated
dataset; they are separate from the later scanner-finding/IDR evaluation.

## Expected validation record

The reviewer should produce a JSON or CSV record with one row per generated
skill, including the filename, base skill, threat type, ground-truth injection,
match status, injection line range, threat-type and placement validity,
unrelated changes, format validity, overall status, confidence, and notes.

All 180 instances passed the five primary checks and were retained in the
paper's RED-generated dataset, $D_{red}$.
