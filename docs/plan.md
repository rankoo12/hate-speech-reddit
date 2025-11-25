Overview

This project collects, enriches, and scores Reddit posts and users discussing controversial, harmful, or violent content.

We will scrape old.reddit.com using requests + BeautifulSoup, analyze content, and produce:

Scored posts feed: language, date_published, post_text, risk_score

Scored risky users feed: username, score, explanation

Enriched user history for approximately two months

Core design decision:

We always scrape the newest posts from selected subreddits (no Reddit search).
We do not pre-filter posts by simple keywords.
Every collected post is scored using a rule-based risk model.
Thresholds on the risk score determine which posts and users are considered risky.

This plan defines the pipeline, architecture, modules, and development steps.

1. Data Collection Strategy (HTML Scraping)

We will not use the Reddit API.
Instead, we scrape old.reddit.com because it is:

Static HTML

Easy to parse

Contains post metadata

Supports pagination

Supports user history pages

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

We do not use Reddit’s search bar.

For each subreddit in target_subreddits:

Start at:
https://old.reddit.com/r/{subreddit}/?sort=new

For each page:

Send a GET request with a custom User-Agent.
Parse <div class="thing"> elements (each represents a post).
Extract:

- post id
- title
- text or selftext (if available)
- author
- subreddit
- timestamp (from <time datetime="...">)
- permalink / URL

Convert each entry into a Post dataclass instance.

Follow the "next page" link for pagination.

Stop when:

- The total number of posts reaches a configured limit (for example: 150 posts in total), or
- We have processed a configured number of pages per subreddit, or
- All posts on the page are older than a lookback window (if enforced at collection time).

Every collected post is later evaluated by the risk scoring model; there is no separate keyword-based discovery filter.

Posts are stored as Post dataclasses and serialized into data/raw_posts.json.

2. Data Enrichment Strategy (User History)

For each unique author from collected posts:

Scrape:

https://old.reddit.com/user/{username}/submitted/
https://old.reddit.com/user/{username}/comments/

Process:

GET HTML.

Parse <div class="thing"> elements.

Extract:

type: submission or comment

subreddit

text or comment body

timestamp

URL/permalink

Convert timestamps to datetimes and keep only items newer than 60 days (approximately 2 months).

Stop when items fall outside the time window or when there are no more pages.

Save as UserPost dataclasses.

3. Risk Scoring Methodology
   3.1 Post-Level Scoring

For each Post.text:

Preprocessing:

- Lowercasing.
- Basic tokenization (split on whitespace and punctuation).

Features include:

Violent keywords

Hate/offensive keywords and slurs

Intensity modifiers (for example: must, should, deserve)

Threat patterns (for example: "I will kill", "we should bomb", "they deserve to die")

All-caps ratio

Keyword density (multiple strong terms in short text)

Scoring algorithm:

Weighted sum of features, normalized to [0, 1].

Produce a breakdown (which features contributed) for explanation purposes.

3.2 User-Level Scoring

Take the user’s last 60 days of posts and comments (all UserPost items).

Compute:

max_post_score

average_score

count_high_posts

Example rule:

user_score = max(max_post_score, average_score + 0.2 \* log(1 + count_high_posts))

Build a natural-language explanation such as:

"4 violent posts in the last 2 months (‘kill’, ‘bomb’). Highest score: 0.93."

4. Edge Cases Handling
   4.1 New User With No History

User-level score equals the highest post-level score from the collected posts.

Explanation: "No additional history; user score derived from collected post(s) only."

4.2 Suspended or Deleted User

User pages return 404 or show restricted content.

History is empty.

Score derived from collected posts only.

Explanation: "User profile not accessible."

4.3 Private Subreddits

Some posts may not be fully accessible.

Store partial data if available.

Explanation can mention incomplete content where relevant.

4.4 Non-English Posts

Use langdetect to detect language.

The risk scoring is tuned for English text; for non-English posts, the model still produces a score but with lower confidence.

Explanation should note the detected language and reduced accuracy.

5. Daily Monitoring Design (Concept)

This is not fully implemented due to assignment scope.

Conceptual design:

Maintain a list of flagged users with:

- username
- last_checked_at
- last_user_score
- last_explanation

Once per day:

Fetch new posts after the last checked timestamp for each flagged user (from submitted and comments pages).

Score new posts.

If a new high-risk post is found, write an entry to an alerts output file (for example data/alerts.csv).

In a production setting, alerts would be pushed to an external system (for example Slack, email, internal dashboards).

This design will be included in the specification document.

6. Project Structure

src/
config.py
models.py (Post, UserPost)
reddit_html_client.py (all scraping)
collector.py
enricher.py
scoring/
vocab.py
post_scoring.py
user_scoring.py
utils/
language.py
timeutils.py
pipeline.py

docs/
PLAN.md
SPEC.pdf
test_plan.md

data/
raw_posts.json
users_enriched.json
posts_scored.csv
users_scored.csv

requirements.txt
README.md

7. Development Steps

Step 1 — Setup

Create feature branch.

Add PLAN.md, config, models, and requirements.

Commit.

Step 2 — HTML Scraper Client

Implement reddit_html_client.py.

Methods:

- fetch_subreddit_new(subreddit: str, max_posts: int)
- get_user_history(username: str, since: datetime)

Manual test with small limits.

Step 3 — Collector

Loop through target_subreddits.

For each subreddit:

- Scrape newest posts using the HTML client.
- Convert raw HTML entries into Post instances.

Store all collected posts in data/raw_posts.json.

Step 4 — Enricher

Identify unique authors.

Fetch user history (last ~60 days) for each author.

Store in users_enriched.json.

Step 5 — Scoring

Implement vocabulary lists and rule-based scoring:

- post-level scoring for each Post and UserPost
- user-level scoring based on user history

Export:

- posts_scored.csv
- users_scored.csv

Step 6 — Documentation and Tests

README: installation and execution instructions.

SPEC.pdf: technical and business specification.

test_plan.md: test strategy and recorded results.

8. Running the Pipeline

Commands (to be implemented in pipeline.py):

python -m src.pipeline collect
python -m src.pipeline enrich
python -m src.pipeline score
python -m src.pipeline all
