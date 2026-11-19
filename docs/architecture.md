# Architecture

> Demo project. All data synthetic and fictional. Not affiliated with any real company.

## Scope and assumptions

### Scoping answers
- **User and problem:** The user is a formulator or R&D scientist at a clean-label ingredient manufacturer, working a goal such as reformulating a product so a label claim survives. For every goal they must juggle at once: which substitute ingredient actually works, what it does to nutrition and cost, whether the label claim holds, and what supply and ESG need to line up behind it. Those answers otherwise live scattered across formula sheets, spec documents, and separate supply and sustainability records.
- **Outcome:** One orchestrated run returns the evidence for the decision instead of a guess. For the `reformulate` goal, the R&D agent flags non-clean-label ingredients, recommends clean-label swaps, predicts texture and shelf-life impact, computes the nutrition panel, validates the label claims per region, and generates the spec and tech sheet; the `full_launch` goal extends the same run to demand forecasting, procurement planning, ESG reporting, and a customer recommendation with pricing bands. A task that fails becomes a failed task result and stops the run — failures are surfaced, not hidden.
- **AI's part of the workflow:** The orchestrator (`core/planner.py`) matches the goal keyword to a declarative plan template (`GOAL_PLANS`) and routes each task to its specialist agent (`rd_formulation`, `supply_chain`, `esg`, `customer_advisor`); task outputs accumulate on a shared blackboard that later tasks read, and the deterministic `FakeLLM` narrates the plan — there is no live model call. The agents prepare and explain the evidence for a decision; they do not themselves release the consequential outputs (see Agency per action). Runs are recorded in the audit log (JSONL) with JSON logging and tracing, and the governance layer scrubs PII and sanitizes free text before it is stored.
- **Agency per action:** Read-only analysis and drafting run autonomously inside a plan: ingredient analysis, substitution ranking, prediction, nutrition, claim checking, and document generation. The consequential outputs never ship on the agent's word alone — `governance/approvals.py` lists the output types that require human approval before release (`new_formulation`, `customer_proposal`, `esg_report`, `production_schedule`, `procurement_plan`): agents propose, humans approve. In this offline demo the gate auto-approves with a clearly marked simulated approver so the demo stays runnable without a human present; in a real deployment the same gate blocks until a human responds. Claim validation can also refuse outright — the regulatory checker rejects a claim the reformulated formula does not support (for example "natural" fails while refined sugar remains).

### Assumptions
- **Data:** All data is synthetic and fictional: `ingredients.json` (55 ingredients), `formulas.json` (8 formulas), `demand.csv`, ESG readings, and the governed glossary (`docs/glossary.md`) that forms the semantic layer. Ingredient names are fictional, and no real company, brand, product, or person data is used anywhere.
- **Inputs:** The system assumes a goal it can route: a keyword that matches a `GOAL_PLANS` template (such as `reformulate` or `full_launch`) and the seeded records those tasks read. The planner raises on an unknown goal rather than improvising a plan, and an unmatched intent is not guessed at — it surfaces as a failure or an escalation path, never an invented answer.
- **Operating constraints:** This is a deterministic offline lab, not a deployed service: no randomness, no network, no API keys, and tests assert exact values, so the demo prints identically on every run. The "LLM" is the deterministic `FakeLLM`, an interface-compatible swap-in point for Azure OpenAI, and the texture/shelf-life predictor is a documented linear demo model, not food science. The Azure mapping in this document is conceptual only — the documented Azure deployment path is validated (`terraform validate`), never applied.
- **Action risk:** The consequential risk is a wrong decision being acted on — an unapproved formulation, customer proposal, production schedule, or ESG report shipping as if it had been checked — rather than damage the agents can do directly, because this demo has no write path into any real system. That risk is contained by making every task output inspectable on the blackboard, by claim validation that can reject, by the approval gate over the five high-impact output types, by scoped-token auth in the governance layer, and by the audit JSONL trail of runs and gate decisions.

## Multi-agent architecture (demo)

```text
                    ┌──────────────────────────────┐
                    │        User / Demo CLI       │
                    │   python -m food_ingredients_ai.demo│
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │   Orchestrator (planner)     │
                    │  - decomposes goal→tasks    │
                    │  - routes to specialist     │
                    │  - blackboard state sharing │
                    └──────┬───┬───┬───┬───────────┘
                           │   │   │   │
        ┌──────────────────┘   │   │   └──────────────────┐
        ▼                      ▼   ▼                      ▼
┌───────────────┐   ┌───────────────┐ ┌───────────┐ ┌──────────────────┐
│ R&D           │   │ Supply Chain  │ │ ESG       │ │ Customer Advisor │
│ Formulation   │   │               │ │           │ │                  │
├───────────────┤   ├───────────────┤ ├───────────┤ ├──────────────────┤
│ - analyzer    │   │ - forecaster  │ │ - collect │ │ - recommender    │
│ - substitution│   │ - inventory   │ │ - carbon  │ │ - sample formula │
│ - predictor   │   │ - scheduler   │ │ - intensity│ │ - claim validator│
│ - nutrition   │   │ - quality     │ │ - report  │ │ - pricing        │
│ - regulatory  │   │               │ │           │ │ - tech sheet     │
│ - docs        │   │               │ │           │ │                  │
└───────┬───────┘   └───────┬───────┘ └─────┬─────┘ └────────┬─────────┘
        └───────────────────┴───────────────┴──────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │   Synthetic data layer       │
                    │  ingredients.json (55)       │
                    │  formulas.json (8)           │
                    │  demand.csv · esg_readings   │
                    │  glossary.md (semantic layer)│
                    └──────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Cross-cutting layers (used by every agent)                       │
├──────────────┬───────────────────┬──────────────────────────────┤
│ Governance   │ Observability     │ Interop                      │
│ - policy     │ - JSON logging    │ - A2A agent cards + tasks    │
│ - HITL gates │ - OTel tracing    │ - MCP server (tools/list)    │
│ - audit JSONL│ - cost/latency    │ - CRM/SAP adapter interfaces │
│ - sanitizer  │ - incident metrics│ - scoped-token auth          │
│ - PII scrub  │                   │                              │
├──────────────┴───────────────────┴──────────────────────────────┤
│ Engineering layers                                               │
│ - rag/ (ingest→embed→retrieve) · context/ (assemble+budget)      │
│ - harness/ (retries/timeouts/circuit breaker)                    │
│ - loops/ (reflection, HITL) · graph/ (nodes/edges/conditionals)  │
└─────────────────────────────────────────────────────────────────┘
```

### How it runs

1. `Orchestrator.plan("reformulate")` matches the goal keyword to a
   declarative plan template (`GOAL_PLANS`) and asks the deterministic
   `FakeLLM` to narrate it.
2. Each `Task` is routed to its registered agent (`rd_formulation`,
   `supply_chain`, `esg`, `customer_advisor`).
3. Task outputs accumulate on a shared **blackboard** dict that later tasks
   read (e.g. substitutions read the analysis flags; claim validation reads
   the reformulated formula and nutrition).
4. Failures become failed `TaskResult`s and stop the run — no exceptions
   escape the orchestrator.

### Conceptual Azure mapping

This repo is intentionally offline, but each piece maps 1:1 to an Azure
deployment discussion:

| Demo component              | Azure equivalent (conceptual)                          |
|-----------------------------|--------------------------------------------------------|
| Orchestrator / planner      | Microsoft Agent Framework (planner + orchestration)    |
| Specialist agents           | Agent Framework agents / Microsoft Foundry agents       |
| Tool functions              | Azure Functions behind Azure API Management            |
| FakeLLM                     | Azure OpenAI (swap-in point; interface-compatible)     |
| ingredients/formulas JSON   | PLM / ingredient DB via Fabric lakehouse               |
| demand.csv                  | SAP IBP via Data Factory → Fabric                      |
| ESG readings                | Plant telemetry / sustainability DB in Fabric          |
| Claim rules                 | Policy engine / regulatory service                     |
| Docs / reports              | Generated artifacts stored in Blob / SharePoint         |
| pytest + CI                 | GitHub Actions (this repo) → Azure DevOps pipelines    |
| Tracing (task results)      | Azure Monitor + Log Analytics                          |
| OTel tracing hooks          | Application Insights (see foundry-deployment §7)        |
| Agent cards / A2A tasks     | Foundry Agent Service inter-agent calls                |
| MCP server                  | External copilots/IDEs invoking domain tools           |
| CRM/SAP demo adapters       | Salesforce/Dynamics, S/4HANA via managed identity      |
| Scoped tokens (demo JWT)    | Entra ID OIDC tokens, workload identity in AKS         |
| In-memory vector store      | Azure AI Search                                        |
| Hash embeddings (offline)   | Azure OpenAI embeddings (live)                         |

### Layer map

| Layer | Purpose | Key modules |
|---|---|---|
| Framework | MAF 1.0 agents, function-tools, WorkflowBuilder | `framework/` |
| Domain agents | Deterministic business logic per specialty | `agents/` |
| Data + semantic | Synthetic datasets + governed glossary | `data/`, `docs/glossary.md` |
| RAG / context | Grounded retrieval, prompt assembly, budgeting | `rag/`, `context/` |
| Harness / loops / graph | Resilient execution, reflection, orchestration | `harness/`, `loops/`, `graph/` |
| Governance | Policy, HITL, audit, security, identity | `governance/` |
| Observability | Logging, tracing, costs, incident metrics | `observability/` |
| Evaluation | Regression + accuracy-style eval suites | `evaluation/`, `evals/` |
| Interop | A2A, MCP, CRM/SAP adapters | `interop/`, `integrations/` |

### Design choices

- **Deterministic everywhere**: no randomness, no network, no API keys.
  Tests assert exact values, and the demo prints identically on every run.
- **Honest heuristics**: the texture/shelf-life "predictor" is a documented
  linear demo model, not food science. It exists to show orchestration, not
  to formulate real products.
- **Claims can fail**: the regulatory checker rejects invalid claims
  (e.g. "natural" fails while refined sugar remains) — a feature, not a bug.
