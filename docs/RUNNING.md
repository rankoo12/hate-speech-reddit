# Running the System

## 1. Requirements

- Python 3.10+
- pip

Install dependencies:

```
pip install -r requirements.txt
```

---

## 2. Virtual Environment (recommended)

### Create venv

```
python -m venv .venv
```

### Activate venv (Windows)

```
.venv\Scripts\activate
```

### Install dependencies

```
pip install -r requirements.txt
```

---

## 3. Running Each Pipeline Stage

### Collect posts

```
python -m src.run_collect
```

### Enrich users

```
python -m src.run_enrich
```

### Score posts

```
python -m src.run_score
```

### Score users

```
python -m src.run_user_score
```

---

## 4. Running the Full Pipeline

```
python -m src.run_pipeline
```

This will generate all outputs under:

```
data/
  raw_posts.json
  users_enriched.json
  posts_scored.csv / jsonl
  users_scored.csv / jsonl
```

---

## 5. Optional: Reddit API PoC

Enable via environment variable:

```
set USE_REDDIT_API=true
```

Required env vars:

```
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USER_AGENT
```

If any are missing, system automatically falls back to HTML scraping.

---

## 6. Data Outputs

All pipeline results are produced inside the `data/` folder.

You may delete and regenerate them using:

```
python -m src.run_pipeline
```
