# Tradeoffs

1. No PDF OCR parsing. I chose CSV and JSON sources so the prototype could focus on realistic intake shapes, provenance, and review flow rather than document extraction.
2. No enterprise RBAC or SSO. That would add a lot of ceremony without changing the core ingestion model, and the assignment weights data model and reasoning more heavily than auth plumbing.
3. No async job queue. The demo seeds and serves data synchronously so it is easy to run locally and easy to defend. A production build would move ingestion to background jobs.