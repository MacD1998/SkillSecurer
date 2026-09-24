# Note Template

Use this template by default. Expand or compress sections depending on the paper, but keep the structure unless there is a strong reason not to.

```markdown
# <Paper title>

## Citation
- Authors:
- Venue / status:
- Year:
- Link:
- Keywords:

## One-paragraph summary
A compact statement of the problem, the core idea, the main result, and why the paper matters.

## Why this paper matters
Explain the gap it addresses and why existing approaches were insufficient.

## Problem setup
- Task / scientific question:
- Inputs / outputs:
- Assumptions:
- Setting / regime:

## Main idea
State the central idea in plain language first, then in technical language.

## Technical core
### Notation and objects
Define the main symbols, variables, operators, and data structures.

### Objective / estimator / algorithm
Write the main formula(s):

$$
\text{insert key equation(s) here}
$$

Explain each term and why it is there.

### Step-by-step mechanism
Walk through the method or argument in order.

### Theoretical claims
If relevant, record theorem statements, assumptions, and proof ideas.

### Complexity / efficiency / identification
Record complexity, sample requirements, identification logic, or resource tradeoffs.

## Evidence
### Experimental or empirical design
Describe datasets, tasks, benchmarks, samples, or environments.

### Main results
Summarize the most important tables / figures.

### Ablations / robustness
Explain what the ablations or robustness checks actually show.

### Baselines and fairness
Were the comparisons strong and fair? Why or why not?

## What I learned from this paper
List the most reusable ideas, techniques, or conceptual distinctions.

## Limitations and failure modes
Be specific. Include hidden assumptions, weak evidence, narrow settings, or possible instability.

## Relationship to other work
Name the closest families of work and explain the connection.

## Open questions
What should be tested, generalized, relaxed, or formalized next?

## Implementation notes
Use this section when implementation details matter.

```python
# pseudocode, training loop sketch, estimator outline,
# or implementation caveats
```

## Verdict
A concise evaluation: what is genuinely strong, what is weak, and whether it deserves to influence future work.
```

## Minimum depth rule

A good note usually contains all of the following:

- one precise statement of the paper's main contribution
- one section that reconstructs the technical mechanism step by step
- one section that evaluates the evidence
- one section on limitations
- one section on connections to nearby literature

## Formula rule

Add formulas when the paper's logic depends on them. Typical triggers:

- the method is defined by an objective or recursion
- the paper introduces a new estimator or update rule
- the theorem depends on specific assumptions or rates
- the experimental design relies on a formal estimand

## Code block rule

Add code blocks when they reduce ambiguity, such as:

- pseudocode for training / inference / estimation
- the exact sequence of operations in a model block
- implementation caveats that are easier to show than describe
