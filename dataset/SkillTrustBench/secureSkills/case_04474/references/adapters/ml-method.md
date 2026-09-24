# Adapter: Methods / ML / Applied Statistics

Use this adapter when the paper proposes a model, objective, estimator, training recipe, operator, inference procedure, or algorithmic mechanism and supports it with experiments or simulations.

## What to prioritize

1. The objective, estimator, state evolution, or update rule.
2. Architecture or representation choices that matter to the result.
3. Training or optimization recipe.
4. Compute, data, and hyperparameter regime.
5. Baselines, ablations, robustness checks, and implementation-sensitive details.
6. Reproducibility: whether a strong practitioner could rebuild the method from the paper.

## Questions to answer in the note

- What is the exact method, not just the intuition?
- Which component is the paper's main move?
- What would the method reduce to if that component were removed?
- Where might the gains really come from: the idea, the scale, or the tuning?
- Are the baselines strong and fairly tuned?
- What details would matter most in a reimplementation?

## Minimum insertions into the note

Add or expand these sections:

### Technical core

- objective function or estimator
- architecture / operator / module description
- training or optimization loop
- complexity or scaling notes

### Evidence

- benchmark setup
- strongest baselines
- ablations tied to the main claim
- robustness or stress tests
- fairness of comparison

### Implementation / reproduction notes

Include:

- training-sensitive details
- preprocessing or augmentation assumptions
- hyperparameters if the paper makes them central
- any missing detail that would block reimplementation

## Special reading rules

- Separate modeling gain from optimization gain.
- Separate methodological gain from scale advantage.
- Check whether a large hidden engineering stack is doing the real work.
- When results look strong, ask whether there are compute, data, or evaluation asymmetries.

## Typical failure patterns to watch for

- weak baselines or mismatched training budgets
- benchmark cherry-picking
- ablations that do not isolate the claimed mechanism
- reproducibility gaps hidden in appendix or code release promises
- novelty resting on recombination of known parts without a clear new mechanism

## Reusable note prompts

- “The decisive design choice is …”
- “The method appears to gain from … rather than …”
- “The strongest evidence for the claimed mechanism is …”
- “A faithful reimplementation would need …”
