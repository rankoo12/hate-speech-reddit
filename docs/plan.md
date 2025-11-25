Overview

This project collects, enriches, and scores Reddit posts and users discussing controversial, harmful, or violent content.

We will scrape old.reddit.com using requests + BeautifulSoup, analyze content, and produce:

Scored posts feed: language, date_published, post_text, risk_score

Scored risky users feed: username, score, explanation

Enriched user history for approximately two months

This plan defines the pipeline, architecture, modules, and development steps.

1. Data Collection Strategy (HTML Scraping)

We will not use the Reddit API.
Instead, we scrape old.reddit.com because it is:

Static HTML

Easy to parse

Contains post metadata

Supports search and pagination

Supports user history pages

1.1 Target Subreddits

Configurable (default):

all

news

worldnews

politics

PublicFreakout

unpopularopinion

1.2 Search Terms

Configurable keywords:

kill

bomb

attack

genocide

racist

hate speech

violent

extremist

terrorist

lynch

1.3 How We Scrape Posts (Discovery Step)

For each (subreddit, query) pair:

Construct URLs such as:

https://old.reddit.com/r/SUBREDDIT/search/?q=kill&restrict_sr=on&sort=new

Or global search:

https://old.reddit.com/search/?q=kill&sort=new

For each search results page:

Send GET request with custom User-Agent.

Parse <div class="thing"> elements.

Extract:

post id

title

text or selftext

author

subreddit

timestamp (from <time datetime="...">)

permalink

Follow "next page" link for pagination.

Stop at a global post cap (for example: 150 posts).

Posts are stored as custom Post dataclasses.

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

Collect items newer than 60 days (approximately 2 months).

Stop when items fall outside the time window.

Save as UserPost dataclasses.

3. Risk Scoring Methodology
   3.1 Post-Level Scoring

Features include:

Violent keywords

Hate keywords

Intensity modifiers

Threat patterns

All-caps ratio

Keyword density

Scoring algorithm:

Weighted sum of features, normalized to [0, 1].

Produce a breakdown for explanation purposes.

3.2 User-Level Scoring

Take the user’s last 60 days of posts and comments.

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

User-level score equals post-level score.

Explanation: "No history; user score derived from post only."

4.2 Suspended or Deleted User

User pages return 404 or show restricted content.

Score derived from post only.

Explanation: "User profile not accessible."

4.3 Private Subreddits

Some posts may not be fully accessible.

Store partial data if available.

4.4 Non-English Posts

Use langdetect to detect language.

Explanation should note reduced accuracy.

5. Daily Monitoring Design (Concept)

This is not fully implemented due to assignment scope.

Conceptual design:

Maintain a list of flagged users.

Once per day:

Fetch new posts after the last checked timestamp.

Score new posts.

If a new high-risk post is found, write an alert to an output file.

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

Create new feature branch.

Add PLAN.md, config, models, and requirements.

Commit.

Step 2 — HTML Scraper Client

Implement reddit_html_client.py.

Methods:

search_posts()

get_user_history()

Manual test with small limits.

Step 3 — Collector

Loop through subreddits and queries.

Fetch posts.

Store in data/raw_posts.json.

Step 4 — Enricher

Identify unique authors.

Fetch user history.

Store in users_enriched.json.

Step 5 — Scoring

Implement vocabulary lists.

Post-level scoring.

User-level scoring.

Export CSV outputs.

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

If this version looks good, you can now:

Create a new branch:
git checkout -b feat/html-scraper

Add docs/PLAN.md

Commit and push it.

Tell me “plan added + branch created” and I’ll guide you into implementing the first real module (config.py + models.py).
