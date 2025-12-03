# GovBot Risk Mitigation Plan (2025-09-03)

This document maps Eticas Deep Dive concerns to concrete mitigations wired into this repo, with owners, success metrics, and tracking.

## 1) Translation Accuracy and Language Representation
- Risks: Inconsistent Kiswahili/Sheng; degraded quality in low-resource languages.
- Mitigations implemented:
  - System prompt updated with multilingual guidance and precision rules (`app/utils/prompts.py`).
  - Standardized multilingual fallbacks created (`app/utils/fallbacks.py`).
  - API accepts `language` hint to steer output (`/chat` endpoints; forwarded to agent).
- Next actions:
  - Fine-tune or swap embeddings for Kiswahili (evaluate multilingual models; pilot bilingual testset).
  - Add language QA tests and glossary checks.
- Owners: AI Lead + Language QA Lead.
- Metrics: Swahili answer BLEU/COMET vs references; human QA pass rate ≥ 90%; no fabricated citations.

## 2) Fallback and Error Handling
- Risks: Underdocumented behavior when retrieval fails or query is ambiguous.
- Mitigations implemented:
  - Standard fallback templates and out-of-scope responses (`fallbacks.py`).
  - No-match/knowledge-gap event logging via `ChatEventService` from chat endpoints.
  - Explicit guidance in system prompt for no-source cases.
- Next actions: Human escalation flow (keyword ‘agent’) routed to service desk.
- Owners: Backend Lead + Support Lead.
- Metrics: No-answer rate; time-to-resolution after escalation; % resolved without hallucinations.

## 3) Unsafe or Invalid Outputs
- Risks: Hallucination, irrelevant or unsafe responses.
- Mitigations implemented:
  - Guardrails in prompt; scope filters in `run_llamaindex_agent` for off-topic queries.
  - Confidence note requirement and no fabricated citations.
- Next actions: Red teaming suite (see Testing Protocol), PII detection filter, jailbreak/prompt-injection tests.
- Owners: Security Lead + AI Lead.
- Metrics: Unsafe output rate < 0.1%; injection test pass rate ≥ 95%.

## 4) Lack of Documentation for Testing
- Risks: No specific docs for red teaming, prompt injection, jailbreak, PII leakage.
- Mitigations implemented:
  - Added `TESTING_PROTOCOLS.md` detailing procedures, datasets, and reporting.
- Next actions: Automate CI steps and dashboards; schedule quarterly red teaming.
- Owners: QA Lead.
- Metrics: Coverage of test categories; mean time to fix; trend of failures ↓ over time.

## 5) Data Currency and Update Mechanisms
- Risks: Unclear update cadence; responsibility; user notification of changes.
- Mitigations implemented:
  - Collection stats endpoints expose latest crawl/indexing timestamps.
  - Knowledge-gap events to drive curation backlog.
- Next actions: Formal update SOP with agency POCs; add “last updated” badges in UI; auto re-index schedule.
- Owners: Data Ops Lead + Agency POCs.
- Metrics: Median document age; SLA for content updates; backlog burn-down.

## 6) Bias and Fairness in Output
- Risks: English/agency over-representation; lower quality in Kiswahili/Sheng.
- Mitigations implemented:
  - Language-aware fallbacks; prompt instructions to avoid overconfident answers without sources.
  - Analytics hooks (ratings, chat events) for fairness dashboards.
- Next actions: Multilingual audit sampling; fairness dashboard in analytics; targeted data augmentation for under-represented topics.
- Owners: Responsible AI Lead.
- Metrics: Parity of answer quality across languages/agencies; representation coverage; complaint rates.

## Tracking & Governance
- Weekly review: Knowledge-gap events, low-confidence responses, and ratings.
- Quarterly audit: Multilingual quality and safety tests.
- RACI: Owners above; PM ensures reporting; DPO oversees PII safeguards.

---

Change log
- 2025-09-03: Initial plan and code hooks (fallbacks, prompt updates, event logging, language parameter).
