Overview

This project collects, enriches, and scores Reddit posts and users discussing controversial, harmful, or violent content.

We scrape old.reddit.com using requests + BeautifulSoup, analyze content, and produce:

Scored posts feed: language, date_published, post_text, risk_score

Scored risky users feed: username, score, explanation

Enriched user history for approximately two months

End-to-end pipeline runnable with one command

Core design decisions:

Scrape newest posts from selected subreddits (no Reddit search).

No keyword pre-filtering during collection.

Every collected post is scored with a rule-based risk model.

Thresholds determine which posts and which users are high-risk.

This plan defines the strategy, architecture, modules, testing approach, and documentation deliverables.

1. Data Collection Strategy (HTML Scraping)

We do not use Reddit’s API for the main pipeline.
We scrape old.reddit.com because it is:

Static HTML

Easy to parse

Contains post metadata

Has simple pagination

Exposes user history pages

1.1 Target Subreddits

Configurable (default):

all

news

worldnews

politics

PublicFreakout

unpopularopinion

Palestine

1.2 How We Scrape Posts (Discovery Step)

For each subreddit:

Start from:
https://old.reddit.com/r/{subreddit}/?sort=new

Parse <div class="thing"> for each post.

Extract:

post id

title

text / selftext

author

subreddit

timestamp

permalink

Follow "next" pagination link until limits reached:

total posts limit

pages per subreddit

age lookback (optional)

Output → data/raw_posts.json

2. Data Enrichment Strategy (User History)

For every unique author from raw posts:

Scrape:

/submitted

/comments

Parse <div class="thing">

Extract:

type (submission / comment)

subreddit

text body

timestamp

url/permalink

Filter last 60 days.

Save as UserPost dataclasses.

Output → data/users_enriched.json

3. Risk Scoring Methodology
   3.1 Post-Level Scoring

Input: Post.text
Features:

Violent keywords

Hate/offensive keywords

Intensifiers

Threat patterns

All-caps ratio

Keyword density

Weighted combination → score ∈ [0,1].

Output includes:

score

label (high/medium/low)

explanation

feature breakdown

3.2 User-Level Scoring

Compute for the user’s last 60 days:

max_post_score

average_score

count_high_posts

total_posts

Formula:

user_score = max(
max_post_score,
average_score + 0.2 \* log(1 + count_high_posts)
)

Explanation example:

"4 high-risk posts in the last 2 months. Highest score: 0.93."

Output → data/users_scored.csv/jsonl

4. Edge Cases Handling
   4.1 New User With No History

Use post-level fallback.

4.2 Suspended/Deleted User

History empty, score derived from posts only.

4.3 Private Subreddits

Partial content handled gracefully.

4.4 Non-English Posts

Language noted, reduced scoring confidence.

5. Optional Reddit API Fallback (Design Only)

We do not use the Reddit API in the main pipeline.
But the system provides a clean abstraction that would allow Reddit API usage if credentials exist.

5.1 Client Abstraction

Define a minimal RedditClient interface:

fetch_new_posts(subreddit, limit) -> List[Post]
fetch_user_history(username, since) -> List[UserPost]

5.2 HTML Client (current implementation)

Uses requests + BeautifulSoup.

Fully implemented & tested.

5.3 API Client (optional stub)

Not executed or tested (no credentials).

Placeholder structure exists.

Allows future extension:

Using praw

Or using OAuth + Reddit API endpoints

5.4 Switching Logic

If env USE_REDDIT_API=true AND credentials exist → API client.
Else → fallback to HTML scraper.

6. Project Structure
   src/
   config.py
   models.py
   reddit_html_client.py
   collector.py
   enricher.py
   scoring/
   vocab.py
   post_scoring.py
   user_scoring.py
   run_collect.py
   run_enrich.py
   run_score.py
   run_user_score.py
   run_pipeline.py ← (NEW) full orchestrator
   data/
   raw_posts.json
   users_enriched.json
   posts_scored.csv / jsonl
   users_scored.csv / jsonl

docs/
PLAN.md
TECH_SPEC.md ← (NEW) technical/business specification
TEST_PLAN.md ← (NEW) testing strategy + results
RUNNING.md ← (NEW) how to run, dependencies

tests/
unit/
smoke/
e2e/
requirements.txt
README.md

7. Development Steps
   Step 1 — Setup

Base config, models, repo structure.

Step 2 — HTML Scraper Client

Implement old.reddit.com scraper.

Step 3 — Collector

Write raw_posts.json.

Step 4 — Enricher

Write users_enriched.json.

Step 5 — Scoring

Post scoring → posts_scored.csv
User scoring → users_scored.csv

Step 6 — Pipeline Runner (NEW)

Single command to run the entire process:

python -m src.run_pipeline

Step 7 — Testing (NEW)
7.1 Unit Tests

post scoring logic

user scoring logic

config/path tests

7.2 Smoke Tests

run_collect with tiny fixtures

run_enrich

run_score

run_user_score

7.3 End-to-End Test

Full pipeline with mocked data; ensure all output files exist and contain valid rows.

Step 8 — Documentation (NEW)
8.1 Technical Specification (PDF)

Objectives, methodology, tools, architecture.

8.2 Test Plan Document

Describe strategy + test cases + results.

8.3 Running Instructions

Dependencies, setup, commands, output paths.

8. Running the Pipeline

Use the orchestrator:

python -m src.run_pipeline

Or run each stage:

python -m src.run_collect
python -m src.run_enrich
python -m src.run_score
python -m src.run_user_score
