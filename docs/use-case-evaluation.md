# Use-Case Evaluation Canvas

A one-page template for deciding whether an AI use case is worth building —
and how to bound it before the first line of code. Fill one canvas per
candidate use case, then compare. Most enterprise AI failures are not model
failures; they are use cases that should never have passed this page.

## 1. Business metric + target

- What business outcome does this move? (e.g. formulation cycle time,
  R&D cost per approved SKU, customer-advisor resolution rate)
- Target: a number with a deadline (e.g. "cut clean-label reformulation
  scoping from 3 weeks to 5 days within two quarters").
- If you cannot name the metric, stop here — this is a demo, not a product.

## 2. Latency budgets (TTFT / TPOT)

- TTFT (time to first token): the responsiveness budget for interactive
  use (e.g. ≤ 1.5 s for advisor chat; batch R&D jobs have no TTFT budget).
- TPOT (time per output token): the throughput budget for long generations
  (e.g. formulation reports must stream ≥ 30 tok/s).
- Measure against the model router's cheapest tier first; only escalate
  tiers when a budget is provably missed.

## 3. Cost-per-inference budget

- Budget per call and per month (e.g. "$0.02/call, $400/mo for the pilot").
- Enforce with per-call tracking and budget caps that block *before* the
  breaching call (see `observability/costs.py`), not with after-the-fact
  dashboards.

## 4. HITL decision — where humans stay in the loop

For each consequential action the agent can take, choose one:

| Action | Mode |
|---|---|
| Read-only analysis / summaries | Autonomous |
| Drafts a human sends (email, report) | Human approves draft |
| Irreversible or regulated action (order, claim, disclosure) | Human approves each action |

Default to the stricter mode; relax only with eval evidence.

## 5. Data readiness check

- Is the data the agent needs reachable, fresh, and governed? (See the
  data-readiness dimensions: completeness, label quality, freshness,
  volume, distribution, governance.)
- Red flags: PII without a masking path, no owner for the source table,
  "we'll clean it during the pilot."

## 6. Maintenance cost-benefit

- Who owns the prompts, evals, and data pipelines after launch? Name them.
- Expected monthly upkeep (eval refresh, prompt tweaks, data drift checks)
  versus the business metric in section 1. If upkeep exceeds ~20% of the
  expected gain, the use case is too fragile for its value.

## 7. Go / no-go

- **Go** only if: metric + target named, budgets set, HITL modes assigned,
  data reachable, owner named.
- **Conditional go**: pilot scoped to one team, one data source, 30 days,
  with the eval suite from day one.
- **No-go**: any blank above is a no-go until filled. A blank is
  information, not a TODO.
