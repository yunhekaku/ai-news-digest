# AI News Digest

A static AI news digest that collects RSS articles, generates a JSON feed, and publishes a React frontend to GitHub Pages.

Live: https://yunhekaku.github.io/ai-news-digest/

## Overview

AI News Digest is a small public web app for quickly scanning AI-related news. A scheduled GitHub Actions workflow fetches RSS entries, generates `articles.json`, builds the frontend, and deploys the static site.

## Tech Stack

- Frontend: React, TypeScript, Vite
- Ingestion: Python, feedparser, BeautifulSoup
- Optional LLM: Gemini API
- Automation: GitHub Actions
- Hosting: GitHub Pages
- Data: static JSON

## Features

- Fetches AI-related RSS feeds
- Generates `frontend/public/articles.json`
- Supports optional Gemini summaries, scores, reasons, and tags
- Falls back to extracted text and keyword-based scoring without an API key
- Reuses the previously deployed `articles.json` as a summary cache
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
| `LLM_PROVIDER` | No | `gemini` or `none`; default is `gemini` |
| `GEMINI_API_KEY` | No | Enables Gemini-generated summaries and metadata |
| `GEMINI_MODEL` | No | Defaults to `gemini-2.5-flash-lite` |
| `MAX_ITEMS` | No | Maximum articles to output; default is `30` |
| `MAX_PER_SOURCE` | No | Maximum RSS entries per source; default is `8` |
| `PUBLIC_ARTICLES_URL` | No | Existing deployed JSON used as a cache |

## Deployment

Deployment is handled by `.github/workflows/pages.yml`.

The workflow runs daily at JST 07:00 and can also be triggered manually from GitHub Actions.
