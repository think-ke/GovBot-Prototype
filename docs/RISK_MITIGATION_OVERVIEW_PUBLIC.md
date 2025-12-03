# GovBot Risk Mitigation Overview (Public Summary)

Date: 2025-09-03

Purpose: Summarize how GovBot addresses the key risks highlighted by Eticas’ Deep Dive, in plain language and without internal code references.

## 1) Translation accuracy and language representation
- Risks
  - Inconsistent Kiswahili/Sheng responses; lower quality in low-resource languages.
- What’s in place
  - Clear multilingual guidance for the assistant (English, Kiswahili, with simple Sheng support).
  - Standardized fallback messages in supported languages when confidence or coverage is low.
  - Client can indicate a preferred language; the assistant adapts tone and terminology accordingly.
- What’s next
  - Evaluate multilingual language models or embeddings specifically for Kiswahili/Sheng.
  - Build bilingual test sets and a terminology/glossary check to reduce mistranslations.
- Success metrics
  - Human QA pass rate ≥ 90% in Kiswahili.
  - No fabricated citations; consistency on core terms.
- Accountable roles
  - AI Lead (quality), Language QA Lead (terminology and testing).

## 2) Fallback and error handling
- Risks
  - Unclear behavior when sources are missing, queries are vague, or topics are out of scope.
- What’s in place
  - Standard “no answer” and “out‑of‑scope” responses that set expectations and suggest next steps.
  - Event logging for knowledge gaps to inform content curation and system improvements.
  - Assistant guardrails steer users back to relevant government topics.
- What’s next
  - Human escalation option (keyword such as “agent”) wired to a service desk and UI handoff.
- Success metrics
  - No‑answer rate (tracked), time‑to‑resolution post‑escalation, and % resolved without hallucinations.
- Accountable roles
  - Backend Lead (implementation), Support Lead (escalation workflow).

## 3) Unsafe or invalid outputs
- Risks
  - Hallucination, unsafe content, or overconfident answers without authoritative sources.
- What’s in place
  - Strong system guardrails (identity, scope, safety) and “no fabrication” policy for citations.
  - Topic scope filters to decline unrelated requests.
  - PII pre‑filter that detects and redacts likely personal data, plus a user warning message.
- What’s next
  - Red teaming suites covering jailbreaks, prompt injection, and PII leakage; add CI gates and reports.
- Success metrics
  - Unsafe output rate < 0.1% in sampled audits; injection/jailbreak pass rate ≥ 95%.
- Accountable roles
  - Security Lead (adversarial testing), AI Lead (model behavior).

## 4) Testing and red teaming documentation
- Risks
  - Lack of clear procedures for safety, fairness, and multilingual testing.
- What’s in place
  - A consolidated testing protocol defining categories, datasets, execution steps, and reporting.
- What’s next
  - Continuous integration automation and periodic red‑team exercises with published summaries.
- Success metrics
  - Coverage across test categories, mean time to fix issues, and downward failure trends.
- Accountable roles
  - QA Lead.

## 5) Data currency and update mechanisms
- Risks
  - Stale content, unclear update cadence, and weak visibility on changes.
- What’s in place
  - Collection/index timestamps and knowledge‑gap signals to steer refresh priorities.
  - Operational hooks to surface “last updated” context to users.
- What’s next
  - Formal update SOP with agency points‑of‑contact; scheduled re‑indexing; visible “last updated” badges.
- Success metrics
  - Median document age, SLA for updates, backlog burn‑down for knowledge gaps.
- Accountable roles
  - Data Ops Lead, Agency POCs.

## 6) Bias and fairness in output
- Risks
  - Over‑representation of English/particular agencies; lower quality in Kiswahili/Sheng.
- What’s in place
  - Language‑aware behavior and careful fallback to avoid overconfident unsupported answers.
  - Ratings and event analytics to enable fairness dashboards and audits.
- What’s next
  - Multilingual audit sampling, fairness dashboard, and targeted data augmentation for under‑represented topics.
- Success metrics
  - Parity of answer quality across languages/agencies, coverage of user needs, and complaint rates.
- Accountable roles
  - Responsible AI Lead.

## Tracking and governance
- Weekly
  - Review knowledge‑gap events, low‑confidence responses, and user ratings; assign remediation actions.
- Quarterly
  - Conduct multilingual quality and safety audits; publish summary findings.
- Roles and oversight
  - Product Manager coordinates reporting; Data Protection Officer oversees PII safeguards and escalation policies.

## Change log
- 2025‑09‑03: Initial public summary reflecting current safeguards, fallbacks, PII measures, and analytics hooks.
