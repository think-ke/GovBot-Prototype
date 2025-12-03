# Fairness and Bias Audits

Goals: Balanced representation across languages (English, Kiswahili, Sheng) and agencies.

## Audit Procedure
- Quarterly sampling: 100 prompts per language per agency.
- Metrics: Answer quality score (human), coverage, citation presence, response time.
- Parity check: Compare metrics across languages/agencies; flag deltas > 10%.

## Data Actions
- Augment under-represented topics (crawl docs, add official FAQs in Kiswahili).
- Improve embeddings/LLMs for Kiswahili.

## Monitoring
- Use ratings, chat events, and analytics to track parity trends.
