# Test Plan

## 1. Testing Strategy

This project uses **unit**, **smoke**, and **end-to-end** (E2E) test layers.

### Unit Tests

Focus on:

- Post scoring logic
- User scoring logic
- Config path resolution
- Reddit API PoC client interface (`isinstance(client, RedditClient)`)

These tests run fast and require no network.

### Smoke Tests (skipped by default)

Validate that each runner can start and process a small dataset:

- `run_collect`
- `run_enrich`
- `run_score`
- `run_user_score`

Disabled by default to avoid network usage during automated testing.

### E2E Test (also skipped)

Runs the entire `run_pipeline`:

1. Fetch posts
2. Enrich users
3. Score posts
4. Score users

Used only in manual evaluation.

---

## 2. Key Unit Test Scenarios

### Post Scoring

- Violent keywords increase score
- Benign text yields low score
- Language detection fallback when unavailable
- Explanation fields are populated

### User Scoring

- Aggregation integrates all post scores
- Users with 0 activity are handled safely
- Thresholds correctly classify `low` / `medium`

### API Client PoC

- Client conforms to `RedditClient` protocol
- Methods exist and return lists
- No real HTTP calls

---

## 3. Running Tests

### Default (unit tests only)

```
pytest
```

### Quiet mode

```
pytest -q
```

### Run a single file

```
pytest tests/unit/test_post_scoring.py
```

### Enable smoke / E2E tests (manual)

Unskip decorators inside relevant tests.

---

## 4. Current Results

- All **unit tests pass**.
- Smoke tests exist but are skipped due to network requirements.
- E2E pipeline test also defined but skipped.

This satisfies assignment requirements for structured testing.
