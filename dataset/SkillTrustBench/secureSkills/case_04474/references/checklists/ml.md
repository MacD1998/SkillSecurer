# Checklist: Methods / ML / Applied Statistics

Run this after the general checklist.

## Method fidelity

- [ ] I stated the exact objective, estimator, recursion, or algorithmic mechanism.
- [ ] I identified the component that is supposed to drive the gain.
- [ ] I explained what the method reduces to without that component.
- [ ] I noted the training or optimization recipe when it materially affects results.

## Evaluation quality

- [ ] I checked whether baselines are strong, current, and fairly tuned.
- [ ] I checked whether there are compute, data, or hyperparameter asymmetries.
- [ ] I identified the strongest ablation that isolates the claimed mechanism.
- [ ] I noted whether robustness checks are narrow, missing, or convincing.

## Reproducibility

- [ ] I recorded implementation-sensitive details that matter for reproduction.
- [ ] I noted any missing details that would block a faithful reimplementation.
- [ ] I distinguished methodological novelty from engineering scale or tuning.

## Skepticism

- [ ] I considered whether the gains could come mostly from more compute, more data, or benchmark choice.
- [ ] I avoided calling the method generally better when the evidence is narrow.
