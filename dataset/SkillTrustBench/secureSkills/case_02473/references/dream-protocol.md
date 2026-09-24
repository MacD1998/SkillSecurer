# Dream Protocol

Dream review is a scheduled consolidation cycle. It does not hallucinate facts; it recombines known material, explores counterfactuals, and produces testable hypotheses.

## Inputs

Load only the relevant files:

- `.cognitive-training/daily/YYYY-MM-DD.md`
- `.cognitive-training/inbox/YYYY-MM-DD.md`
- `.cognitive-training/cards.md` entries created or reviewed today
- `.cognitive-training/mistakes.md` open entries
- `.cognitive-training/graph.md` recent links
- `.learnings/` if present
- `tian-dao` skill body or references if available

## Dream Stages

### 1. Replay

Summarize the day as factual observations:

- What happened?
- What was learned?
- What failed?
- What remains unresolved?

Label these as `Observation`, not conclusion.

### 2. Compression

Reduce the day into 3-7 fragments:

- one central concept
- one procedure or workflow
- one mistake or correction
- one open question
- one analogy or cross-domain connection
- one strategic implication

### 3. Tian-Dao Deduction

For each important fragment, run the eight dimensions:

| Dimension | Dream Question |
| --- | --- |
| Causal chain | What caused this learning, and what will it change? |
| Forces | Which user needs, tools, constraints, incentives, or agents are involved? |
| Variables | What variables could change the interpretation? |
| Branch points | What decisions or evidence would split the future path? |
| Probability | Which branches are most likely, and how confident are we? |
| Timeline | When should this be reviewed, tested, or applied? |
| Butterfly effect | Which small detail could compound into a large future gain or failure? |
| Terminal state | What does mastery, stagnation, and failure look like? |

Then apply:

- Contradiction analysis: identify the main contradiction and secondary contradictions.
- Practice theory: decide what must be tested in action.
- Inversion: imagine the lesson failed and reverse-engineer why.
- Safety margin: preserve uncertainty and avoid over-promoting weak insights.

### 4. Academic Rigor Pass

Write every important result as one of:

- `Observation`: directly seen in today's work.
- `Inference`: reasoned from observations.
- `Hypothesis`: plausible but needs evidence.
- `Speculation`: useful idea with weak evidence.

For each hypothesis, include:

```markdown
- Hypothesis:
- Why it might be true:
- What would falsify it:
- Evidence to seek:
- Confidence: low | medium | high
- Next experiment:
```

### 5. Recombination

For each fragment, produce:

- near transfer: same domain, new task
- far transfer: different domain, similar structure
- counterexample: where the idea breaks
- research question: what to study next

### 6. Promotion Gate

Do not promote dream outputs directly into durable principles unless one of these is true:

- user explicitly confirms it
- it was validated by a later task
- it survived at least one review cycle
- it corrects a repeated mistake

Unvalidated outputs become cards with `Source: dream` and `Stability: new`.

## Output File

Write to `.cognitive-training/dreams/YYYY-MM-DD.md`:

```markdown
# Dream Review YYYY-MM-DD

## Inputs

## Replay

## Compressed Fragments

## Tian-Dao Deduction

## Academic Rigor Pass

## Recombination

## Hypotheses To Test

## Updates Proposed
```
