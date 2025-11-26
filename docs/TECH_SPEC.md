# Technical & Business Specification

## 1. Overview

This system collects Reddit posts from selected subreddits, enriches them with user history, and applies scoring logic to classify harmful or violent content. The final output includes structured, review-ready datasets of both posts and users.

Primary data collection is performed through HTML scraping of **old.reddit.com**, using `requests` and `BeautifulSoup`.  
A **feature-flagged Reddit API fallback** exists as a minimal PoC only.

---

## 2. Business Context

Modern trust & safety workflows require early detection of harmful content:

- Violent or abusive language
- High-risk user behavior patterns
- Scalable and explainable scoring
- Structured datasets for moderators and analysts

This system provides:

- Automated ingestion of new posts
- Historical behavioral context via enrichment
- Rule-based risk scoring
- Exportable CSV/JSON feeds

---

## 3. Data Collection

### Approach

- Scrape `/r/<subreddit>/?sort=new` for newest posts.
- Extract metadata: ID, author, title, body text, timestamp.
- Retry logic + pagination support.
- Configurable per-sub and global post limits.

### Why HTML scraping?

- Assignment requirement.
- Publicly accessible.
- Stable structure.
- No login or API authentication.

### User history

- Scrape `/user/<username>/submitted` and `/user/<username>/comments`
- Cap results (submissions + comments)
- Enforce a lookback window (e.g., 60 days)
- Output includes:
  - Recent posts
  - Recent comments
  - Total count

---

## 4. Enrichment

`enricher.py` loads `raw_posts.json`, identifies unique authors, and fetches their activity streams using the HTML client.

Enrichment adds:

- Submissions and comments
- Timestamps in UTC
- Basic filtering and ordering
- Structured output: `users_enriched.json`

Goal: provide historical context for user-level scoring.

---

## 5. Scoring

### Post Scoring

Implemented in `src/scoring/post_scoring.py`.

- Keyword-based heuristics (violent / harmful vocabulary)
- Simple language detection
- Rule-based scoring → 0–1 risk score
- Labels: `low`, `medium`, `high`
- Includes explanations and per-feature values

Outputs:

- `posts_scored.csv`
- `posts_scored.jsonl`

### User Scoring

Implemented in `src/scoring/user_scoring.py`.

Uses aggregated post metrics:

- Maximum post score
- Average score
- Count of high-risk posts
- Total posts considered

Produces:

- Final user risk score
- `low` or `medium` label
- Explanation for reviewers

Outputs:

- `users_scored.csv`
- `users_scored.jsonl`

---

## 6. Architecture & Tools

### Key Modules

```
src/
  collector.py
  enricher.py
  scoring/
    post_scoring.py
    user_scoring.py
  clients/
    reddit_client.py
    __init__.py
  reddit_html_client.py
  run_collect.py
  run_enrich.py
  run_score.py
  run_user_score.py
  run_pipeline.py
```

### Tools & Libraries

- Python 3
- `requests`
- `BeautifulSoup`
- `langdetect`
- `pytest`
- `json` & `csv`

### Runners

- `run_collect` → fetch new posts
- `run_enrich` → enrich users
- `run_score` → score posts
- `run_user_score` → score users
- `run_pipeline` → full pipeline

---

## 7. Outputs & Data Products

### `raw_posts.json`

Scraped posts with metadata.

### `users_enriched.json`

User activity: submissions + comments.

### `posts_scored.*`

Risk scores for each post.

### `users_scored.*`

Aggregated risk scores for users.

All outputs live in the `data/` directory.

---

## 8. Optional Reddit API PoC

A minimal, disabled-by-default demonstration of how an API-based client would plug into the system.

### How it works

- `RedditClient` protocol defines required methods.
- `RedditHtmlClient` = full implementation.
- `RedditApiClient` = PoC (returns empty lists).
- Controlled by:

```
USE_REDDIT_API=true
```

Requires environment variables:

```
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USER_AGENT
```

If any missing → fallback to HTML scraping.

---

## 9. Limitations

- No real Reddit API usage
- Rule-based scoring (not ML)
- HTML structure assumptions
- Not optimized for very large-scale ingestion

---

## 10. Conclusion

This pipeline demonstrates a complete, explainable workflow for collecting, enriching, and scoring potentially harmful Reddit content. It is modular, testable, and easily extended, while following the assignment constraints.
