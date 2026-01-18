---
name: notion-to-x-publisher
description: Fetch Notion articles by slug or page ID and publish to X Articles. Use when user wants to publish Notion content to X, mentions "Notion to X", "publish Notion article to Twitter", "把 Notion 文章发到 X", or wants to fetch a Notion page and post to X Articles. This skill handles the COMPLETE workflow from Notion to X draft - no need to invoke other skills separately.
---

# Notion to X Publisher

Fetch articles from Notion by slug or page ID, convert to Markdown with images, and publish to X Articles editor.

**这是一个端到端的 Skill**：当用户要求发布 Notion 文章到 X 时，按照本文档的完整流程执行，无需用户额外指示。

## Quick Start (完整流程概览)

当用户说 "把 slug xxx 发布到 X" 或 "publish Notion page abc123 to X" 时，执行以下完整流程：

```bash
# Phase 1: 获取 Notion 文章
python ~/.claude/skills/notion-to-x-publisher/scripts/fetch_notion_article.py \
  --slug "<slug>" --output-dir /tmp/notion_article
# 或 --page-id "<page_id>"

# Phase 2: 解析 Markdown（使用 x-article-publisher 脚本）
python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  /tmp/notion_article/<slug>.md > /tmp/article.json

python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  /tmp/notion_article/<slug>.md --html-only > /tmp/article_html.html

# Phase 3: 浏览器自动化发布（按 x-article-publisher 流程）
# 1. browser_navigate: https://x.com/compose/articles
# 2. Click "create" button
# 3. Upload cover image (browser_file_upload)
# 4. Fill title
# 5. Copy HTML to clipboard & paste
# 6. Insert content images at block positions (reverse order)
# 7. Save draft
```

## Prerequisites

- Playwright MCP for browser automation
- User logged into X with Premium Plus subscription
- Python 3.9+ with dependencies:
  - macOS: `pip install Pillow pyobjc-framework-Cocoa notion-client`
  - Windows: `pip install Pillow pywin32 clip-util notion-client`
- x-article-publisher skill installed (for clipboard and parsing scripts)
- Environment variables:
  - `NOTION_TOKEN`: Notion integration token
  - `DATABASE_ID`: Notion database ID (optional, for slug lookup)

## Scripts

Located in `~/.claude/skills/notion-to-x-publisher/scripts/`:

### fetch_notion_article.py

Fetch a Notion article and convert to Markdown:

```bash
# By page ID
python fetch_notion_article.py --page-id <notion_page_id>

# By slug (requires DATABASE_ID)
python fetch_notion_article.py --slug <article_slug>

# With output directory for images
python fetch_notion_article.py --page-id <id> --output-dir /tmp/notion_article
```

**Output JSON:**
```json
{
  "title": "Article Title",
  "slug": "article-slug",
  "markdown": "# Article Title\n\nContent with images...",
  "markdown_file": "/tmp/notion_article/article.md",
  "images": [
    {"original_url": "https://...", "local_path": "/tmp/notion_article/images/image_001.png", "type": "external"},
    {"original_url": "https://prod-files...", "local_path": "/tmp/notion_article/images/image_002.jpg", "type": "notion_file"}
  ],
  "cover_image": "/tmp/notion_article/images/cover.jpg"
}
```

**Key features:**
- Downloads both external URLs and Notion file URLs
- Handles Notion's temporary signed URLs for files
- Replaces image URLs in Markdown with local paths
- Extracts cover image from page

## Workflow

**一键发布流程 (One-Command Publishing)**

1. Fetch Notion article → Markdown + local images
2. Use x-article-publisher workflow to publish Markdown to X

### Step 1: Fetch Notion Article

```bash
# By slug
python ~/.claude/skills/notion-to-x-publisher/scripts/fetch_notion_article.py \
  --slug "my-article-slug" \
  --output-dir /tmp/notion_article

# By page ID
python ~/.claude/skills/notion-to-x-publisher/scripts/fetch_notion_article.py \
  --page-id "abc123..." \
  --output-dir /tmp/notion_article
```

### Step 2: Parse Markdown (using x-article-publisher)

```bash
python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  /tmp/notion_article/article.md > /tmp/article.json

python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  /tmp/notion_article/article.md --html-only > /tmp/article_html.html
```

### Step 3: Publish to X (using x-article-publisher workflow)

Follow the x-article-publisher SKILL.md workflow:
1. Navigate to https://x.com/compose/articles
2. Click "create" button
3. Upload cover image
4. Fill title
5. Paste HTML content
6. Insert content images at block positions
7. Save draft

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| NOTION_TOKEN | Yes | Notion integration token |
| DATABASE_ID | For slug lookup | Notion database ID containing articles |

### 三种配置方式（优先级从高到低）：

1. **命令行参数**（最高优先级）：
   ```bash
   python fetch_notion_article.py --slug xxx --notion-token "secret_xxx" --database-id "abc123"
   ```

2. **环境变量**：
   ```bash
   export NOTION_TOKEN="secret_xxx..."
   export DATABASE_ID="abc123..."
   ```

3. **.env 文件**（自动加载）：
   - 当前工作目录的 `.env`
   - 用户主目录的 `~/.env`
   - skill 目录的 `.env`
   
   或通过 `--env-file` 指定：
   ```bash
   python fetch_notion_article.py --slug xxx --env-file /path/to/.env
   ```

### .env 文件格式：

```bash
# Notion credentials
NOTION_TOKEN=secret_xxx...
DATABASE_ID=abc123...
```

## Example Usage

### User Request Examples:

```
"发布 Notion 文章 my-article-slug 到 X"
"Publish my Notion article with page ID abc123 to X Articles"
"把 Notion 里的这篇文章发到推特: xxx"
```

### Full Workflow Example:

```bash
# Step 1: Fetch from Notion (by slug)
python ~/.claude/skills/notion-to-x-publisher/scripts/fetch_notion_article.py \
  --slug "ai-tools-2024" \
  --output-dir /tmp/notion_article

# Step 2: Parse Markdown for X
python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  /tmp/notion_article/article.md > /tmp/article.json

python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  /tmp/notion_article/article.md --html-only > /tmp/article_html.html

# Step 3: Use browser automation to publish (follow x-article-publisher flow)
# ... (browser navigation, image upload, paste HTML, etc.)
```

## Image Handling

### Supported Image Types

1. **External Images**: Regular URLs (https://example.com/image.jpg)
   - Downloaded directly via HTTP

2. **Notion File Images**: Notion-hosted files (https://prod-files-secure.s3.us-west-2.amazonaws.com/...)
   - Uses signed URLs with expiration
   - Must be downloaded before URLs expire (typically 1 hour)

### Image Processing

- All images are downloaded to `{output_dir}/images/`
- Markdown is updated to use local paths
- Image filenames are sanitized and numbered (image_001.png, etc.)
- Cover image is saved separately as `cover.{ext}`

## Critical Rules

1. **NEVER publish** - Only save draft on X
2. **Download images first** - Notion signed URLs expire
3. **Validate content** - Check Markdown output before publishing
4. **Use existing scripts** - Reuse x-article-publisher scripts for parsing/clipboard

## Troubleshooting

### "Page not found" Error
- Verify page ID is correct (32-char hex)
- Ensure Notion integration has access to the page

### "Slug not found" Error
- Check DATABASE_ID is set correctly
- Verify slug exists in database and status is not "draft"

### Image Download Failed
- Notion file URLs expire after ~1 hour
- Re-run fetch to get fresh signed URLs

### Empty Content
- Check if page has content blocks
- Verify integration has read access to page content

---

## 完整执行指南 (End-to-End Execution Guide)

**当用户请求发布 Notion 文章到 X 时，按以下步骤完整执行：**

### Phase 1: 获取 Notion 文章

```bash
# 确定输出目录
OUTPUT_DIR="/tmp/notion_article"

# 按 slug 获取（如果用户提供了 slug）
python ~/.claude/skills/notion-to-x-publisher/scripts/fetch_notion_article.py \
  --slug "<user_provided_slug>" \
  --output-dir $OUTPUT_DIR

# 或按 page ID 获取（如果用户提供了 page ID）
python ~/.claude/skills/notion-to-x-publisher/scripts/fetch_notion_article.py \
  --page-id "<user_provided_page_id>" \
  --output-dir $OUTPUT_DIR
```

**从输出 JSON 中获取：**
- `markdown_file`: Markdown 文件路径
- `cover_image`: 封面图路径
- `title`: 文章标题

### Phase 2: 解析 Markdown

```bash
# 获取结构化数据
python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  $OUTPUT_DIR/<slug>.md > /tmp/article.json

# 生成 HTML 用于粘贴
python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  $OUTPUT_DIR/<slug>.md --html-only > /tmp/article_html.html
```

**从 article.json 中获取：**
- `title`: 标题
- `cover_image`: 封面图（可能与 Phase 1 不同，以此为准）
- `content_images`: 内容图片数组（含 block_index）
- `total_blocks`: 总块数

### Phase 3: 浏览器自动化发布

按照 x-article-publisher SKILL.md 的详细步骤执行：

#### Step 1: 打开 X Articles 编辑器
```
browser_navigate: https://x.com/compose/articles
browser_snapshot  # 找到 create 按钮
browser_click: create button
```

#### Step 2: 上传封面图
```
browser_click: "添加照片或视频" button
browser_file_upload: <cover_image_path>
browser_click: 应用 button
```

#### Step 3: 填写标题
```
browser_type: element="添加标题" textbox, text="<title>"
```

#### Step 4: 粘贴正文
```bash
# 复制 HTML 到剪贴板
python ~/.claude/skills/x-article-publisher/scripts/copy_to_clipboard.py \
  html --file /tmp/article_html.html
```
```
browser_click: editor textbox
browser_press_key: Meta+v
```

#### Step 5: 插入内容图片（按 block_index 从大到小）

对于每张图片（从 content_images 数组，按 block_index 降序）：

```bash
# 复制图片到剪贴板
python ~/.claude/skills/x-article-publisher/scripts/copy_to_clipboard.py \
  image <image_path> --quality 85
```
```
browser_snapshot  # 找到对应 block
browser_click: block element at block_index position
browser_press_key: Meta+v
browser_wait_for: textGone="正在上传媒体" time=2
```

#### Step 6: 保存草稿
```
# 草稿自动保存，验证内容
browser_snapshot
# 报告: "草稿已保存。请手动检查并发布。"
```

### 自然语言触发示例

用户可能这样说：
- "把 slug my-article 发布到 X"
- "发布 Notion 文章 abc123 到推特"
- "Publish my Notion article to X: my-article-slug"
- "把这篇 Notion 文章发到 X Articles: page-id-xxx"

**识别到这些请求时，自动执行上述完整流程。**

### 执行原则

1. **不要询问** - 直接按流程执行
2. **不要分步确认** - 一次性完成所有步骤
3. **只保存草稿** - 永远不要自动发布
4. **报告结果** - 完成后告知用户草稿已保存
