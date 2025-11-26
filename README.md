# Hate-Speech Reddit Analysis Pipeline

This repository implements a full pipeline for:

1. Collecting Reddit posts
2. Enriching with user history
3. Scoring posts for harmful/violent content
4. Scoring users based on aggregated risk
5. Producing CSV/JSON outputs for review

The system uses **HTML scraping from old.reddit.com** (as required by the assignment).  
A **Reddit API fallback** is included as a minimal PoC.

---

## Documentation

- [Technical Specification](docs/TECH_SPEC.md)
- [Test Plan](docs/TEST_PLAN.md)
- [Running Instructions](docs/RUNNING.md)

---

## Quickstart

```
pip install -r requirements.txt
python -m src.run_pipeline
```

Outputs go to the `data/` directory.

---

## Key Features

- Robust subreddit collection
- User history enrichment
- Rule-based scoring
- JSONL and CSV output feeds
- Modular components (`collector`, `enricher`, `scoring`)
- Optional API PoC via `USE_REDDIT_API=true`

---

## Project Status

✔ All unit tests passing  
✔ Pipeline fully runnable  
✔ Documentation complete  
✔ Optional API fallback integrated
