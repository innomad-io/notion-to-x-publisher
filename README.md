# Notion to X Publisher Skill

Fetch articles from Notion by slug or page ID and publish to X (Twitter) Articles with one command.

[English](README.md) | [中文](README_CN.md)

---

> **⚠️ Dependency Notice**
> 
> This skill depends on [x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill) by [@wshuyi](https://github.com/wshuyi) for the X Articles publishing workflow and clipboard scripts.
> 
> Special thanks to **wshuyi** for creating the excellent x-article-publisher skill that makes this integration possible! 🙏

---

## The Problem

Publishing Notion content to X Articles involves:
1. Copy content from Notion
2. Lose all formatting
3. Manually reformat in X editor
4. Upload images one by one
5. Position images correctly

**This skill automates the entire process.**

---

## Features

- **Fetch by Slug or Page ID**: Flexible article lookup
- **Image Support**: Downloads both external URLs and Notion-hosted files
- **Automatic Markdown Conversion**: Rich text, headings, lists, code blocks
- **LaTeX Support**: Preserves mathematical equations
- **One Command Publishing**: Combines fetching and publishing

---

## Requirements

| Requirement | Details |
|-------------|---------|
| Claude Code | [claude.ai/code](https://claude.ai/code) |
| Playwright MCP | Browser automation |
| X Premium Plus | Required for Articles feature |
| Python 3.9+ | With dependencies below |
| x-article-publisher | For X publishing workflow |

```bash
# Install dependencies
pip install notion-client Pillow

# macOS additional
pip install pyobjc-framework-Cocoa

# Windows additional
pip install pywin32 clip-util
```

---

## Installation

### Method 1: Git Clone

```bash
git clone https://github.com/your-username/notion-to-x-publisher-skill.git
cp -r notion-to-x-publisher-skill/skills/notion-to-x-publisher ~/.claude/skills/
```

### Method 2: Manual Copy

Copy the `notion-to-x-publisher` folder to `~/.claude/skills/`

---

## Configuration

Three ways to provide credentials (priority order):

### 1. Command Line Arguments (highest priority)
```bash
python fetch_notion_article.py --slug xxx --notion-token "secret_xxx" --database-id "abc123"
```

### 2. Environment Variables
```bash
export NOTION_TOKEN="secret_xxx..."
export DATABASE_ID="abc123..."
```

### 3. .env File (auto-loaded)

Create `.env` in current directory, `~/.env`, or skill directory:
```bash
NOTION_TOKEN=secret_xxx...
DATABASE_ID=abc123...
```

Or specify path:
```bash
python fetch_notion_article.py --slug xxx --env-file /path/to/.env
```

---

## Usage

### Natural Language

```
Publish Notion article "my-article-slug" to X
```

```
Fetch Notion page abc123 and post to X Articles
```

```
把 Notion 文章发布到推特: my-article-slug
```

### Manual Steps

```bash
# Step 1: Fetch from Notion
python ~/.claude/skills/notion-to-x-publisher/scripts/fetch_notion_article.py \
  --slug "my-article" \
  --output-dir /tmp/notion_article

# Step 2: Parse for X (using x-article-publisher)
python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  /tmp/notion_article/my-article.md

# Step 3: Follow x-article-publisher workflow to publish
```

---

## Workflow

```
Notion Page
     ↓ fetch_notion_article.py
Markdown + Local Images
     ↓ parse_markdown.py (x-article-publisher)
Structured Data (title, images, HTML)
     ↓ Playwright MCP
X Articles Editor
     ↓
Draft Saved
```

---

## Script Reference

### fetch_notion_article.py

```bash
# By page ID
python fetch_notion_article.py --page-id <id>

# By slug
python fetch_notion_article.py --slug <slug>

# With custom output directory
python fetch_notion_article.py --slug <slug> --output-dir /path/to/output
```

**Output JSON:**
```json
{
  "title": "Article Title",
  "slug": "article-slug",
  "markdown": "# Article Title\n\n...",
  "markdown_file": "/tmp/notion_article/article.md",
  "images": [
    {"original_url": "...", "local_path": "...", "type": "external"}
  ],
  "cover_image": "/tmp/notion_article/images/cover.jpg"
}
```

---

## Database Requirements

For slug lookup, your Notion database should have:

| Property | Type | Description |
|----------|------|-------------|
| title | Title | Article title |
| slug | Rich Text | URL-friendly slug |
| status | Select | Publication status (not "draft") |

---

## Image Handling

### Supported Types

1. **External Images**: Regular URLs (e.g., Unsplash, CDN)
2. **Notion Files**: Notion-hosted images with signed URLs

### How It Works

1. Detect image type from block structure
2. Download to local `images/` folder
3. Replace URLs in Markdown with local paths
4. Cover image saved as `cover.{ext}`

---

## Project Structure

```
notion-to-x-publisher/
├── SKILL.md              # Skill instructions
├── README.md             # This file
├── README_CN.md          # Chinese version
└── scripts/
    └── fetch_notion_article.py
```

---

## Dependencies

This skill works with:
- **x-article-publisher**: Provides X publishing workflow and clipboard scripts

Make sure x-article-publisher is installed at `~/.claude/skills/x-article-publisher/`

---

## Troubleshooting

### "NOTION_TOKEN is required"
Set the environment variable or pass `--notion-token` flag.

### "DATABASE_ID is required for slug lookup"
Set the environment variable or pass `--database-id` flag.

### "Article with slug 'xxx' not found"
- Verify the slug exists in your database
- Check the article status is not "draft"
- Ensure Notion integration has database access

### Image download failed
- Notion signed URLs expire after ~1 hour
- Re-run fetch to get fresh URLs

---

## License

MIT License

## Author

Works with [x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill)

---

## Contributing

- **Issues**: Report bugs or request features
- **PRs**: Welcome! Especially for Windows support
