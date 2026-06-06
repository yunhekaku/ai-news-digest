# AI News Digest

A static AI news digest that collects RSS articles, generates a JSON feed, and publishes a React frontend to GitHub Pages.

Live: https://yunhekaku.github.io/ai-news-digest/

## Overview

AI News Digest is a small public web app for quickly scanning AI-related news. A scheduled GitHub Actions workflow fetches RSS entries, generates `articles.json`, builds the frontend, and deploys the static site.

## Tech Stack

- Frontend: React, TypeScript, Vite
- Ingestion: Python, feedparser, BeautifulSoup
- Optional LLM: Anthropic API
- Automation: GitHub Actions
- Hosting: GitHub Pages
- Data: static JSON

## Features

- Fetches AI-related RSS feeds
- Generates `frontend/public/articles.json`
- Supports optional LLM summaries, scores, reasons, and tags
- Falls back to extracted text and keyword-based scoring without an API key
- Displays articles sorted by importance or publish date
- Deploys automatically to GitHub Pages

## Project Structure

```txt
ai-news-digest/
├── frontend/
│   ├── public/articles.json
│   └── src/
├── scripts/
│   ├── ingest.py
│   └── requirements.txt
├── .github/workflows/pages.yml
└── docs/architecture.md
```

## Local Development

Generate article data:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/ingest.py
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Local URL:

```txt
http://localhost:3000
```

## Environment Variables

| Variable | Required | Description |
|---|---:|---|
| `ANTHROPIC_API_KEY` | No | Enables LLM-generated summaries and metadata |
| `ANTHROPIC_MODEL` | No | Defaults to `claude-3-5-haiku-latest` |
| `MAX_ITEMS` | No | Maximum articles to output; default is `30` |
| `MAX_PER_SOURCE` | No | Maximum RSS entries per source; default is `8` |

## Deployment

Deployment is handled by `.github/workflows/pages.yml`.

The workflow runs daily at JST 07:00 and can also be triggered manually from GitHub Actions.
