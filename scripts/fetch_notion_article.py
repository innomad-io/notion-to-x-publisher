#!/usr/bin/env python3
"""
Fetch Notion article by slug or page ID and convert to Markdown with images.

Usage:
    python fetch_notion_article.py --page-id <page_id> [--output-dir <dir>]
    python fetch_notion_article.py --slug <slug> [--output-dir <dir>]
    
Environment variables (can be set via .env file, command line, or shell):
    NOTION_TOKEN: Notion integration token (required)
    DATABASE_ID: Notion database ID (required for slug lookup)
"""

import argparse
import json
import os
import re
import sys
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


def load_dotenv():
    """Load environment variables from .env file (lightweight implementation)."""
    # Search for .env file in current directory and parent directories
    env_paths = [
        Path.cwd() / ".env",
        Path.home() / ".env",
        Path(__file__).parent.parent / ".env",  # skill directory
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if not line or line.startswith("#"):
                            continue
                        # Parse KEY=VALUE
                        if "=" in line:
                            key, _, value = line.partition("=")
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes if present
                            if (value.startswith('"') and value.endswith('"')) or \
                               (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                            # Only set if not already in environment
                            if key and key not in os.environ:
                                os.environ[key] = value
                print(f"Loaded environment from: {env_path}", file=sys.stderr)
                return True
            except Exception as e:
                print(f"Warning: Failed to load {env_path}: {e}", file=sys.stderr)
    
    return False


# Load .env file before other imports that might need env vars
load_dotenv()


try:
    from notion_client import Client
except ImportError:
    print("Error: notion-client not installed. Run: pip install notion-client", file=sys.stderr)
    sys.exit(1)


class NotionArticleFetcher:
    """Fetch and convert Notion articles to Markdown."""
    
    def __init__(self, token: str, database_id: Optional[str] = None):
        self.client = Client(auth=token)
        self.database_id = database_id
        self.images = []
        self.image_counter = 0
        
    def fetch_by_page_id(self, page_id: str, output_dir: str) -> dict:
        """Fetch article by Notion page ID."""
        # Normalize page ID (remove hyphens if present)
        page_id = page_id.replace("-", "")
        
        # Get page metadata
        page = self.client.pages.retrieve(page_id=page_id)
        
        return self._process_page(page, output_dir)
    
    def fetch_by_slug(self, slug: str, output_dir: str) -> dict:
        """Fetch article by slug from database."""
        if not self.database_id:
            raise ValueError("DATABASE_ID is required for slug lookup")
        
        # Query database for the slug
        response = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "and": [
                    {
                        "property": "slug",
                        "rich_text": {"equals": slug}
                    },
                    {
                        "property": "status",
                        "select": {"does_not_equal": "draft"}
                    }
                ]
            }
        )
        
        if not response["results"]:
            raise ValueError(f"Article with slug '{slug}' not found")
        
        page = response["results"][0]
        return self._process_page(page, output_dir)
    
    def _process_page(self, page: dict, output_dir: str) -> dict:
        """Process a Notion page and convert to Markdown."""
        output_path = Path(output_dir)
        images_dir = output_path / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Reset image tracking
        self.images = []
        self.image_counter = 0
        
        # Extract metadata
        properties = page.get("properties", {})
        title = self._extract_plain_text(properties.get("title", {}).get("title", []))
        if not title:
            title = self._extract_plain_text(properties.get("Name", {}).get("title", []))
        
        slug = self._extract_plain_text(properties.get("slug", {}).get("rich_text", []))
        
        # Extract cover image
        cover_image = None
        cover = page.get("cover")
        if cover:
            cover_url = self._get_image_url(cover)
            if cover_url:
                cover_ext = self._get_extension(cover_url)
                cover_path = images_dir / f"cover{cover_ext}"
                if self._download_image(cover_url, str(cover_path)):
                    cover_image = str(cover_path)
                    self.images.append({
                        "original_url": cover_url,
                        "local_path": str(cover_path),
                        "type": "cover"
                    })
        
        # Get page content blocks
        blocks = self._get_all_blocks(page["id"])
        
        # Convert to Markdown
        markdown = self._blocks_to_markdown(blocks, images_dir)
        
        # Add title as H1 if present
        if title:
            markdown = f"# {title}\n\n" + markdown
        
        # Add cover image after title if present
        if cover_image:
            markdown = markdown.replace(f"# {title}\n\n", f"# {title}\n\n![cover]({cover_image})\n\n", 1)
        
        # Save markdown file
        md_filename = f"{slug or 'article'}.md"
        md_path = output_path / md_filename
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        return {
            "title": title,
            "slug": slug,
            "markdown": markdown,
            "markdown_file": str(md_path),
            "images": self.images,
            "cover_image": cover_image
        }
    
    def _get_all_blocks(self, block_id: str) -> list:
        """Get all blocks from a page with pagination."""
        blocks = []
        cursor = None
        
        while True:
            response = self.client.blocks.children.list(
                block_id=block_id,
                start_cursor=cursor,
                page_size=100
            )
            blocks.extend(response["results"])
            
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
        
        return blocks
    
    def _blocks_to_markdown(self, blocks: list, images_dir: Path, depth: int = 0) -> str:
        """Convert Notion blocks to Markdown."""
        lines = []
        indent = "  " * depth
        
        for block in blocks:
            block_type = block.get("type")
            md = self._block_to_markdown(block, images_dir, depth)
            
            if md:
                lines.append(md)
            
            # Handle children if present
            if block.get("has_children"):
                children = self._get_all_blocks(block["id"])
                child_depth = depth + 1 if block_type in ["bulleted_list_item", "numbered_list_item", "to_do"] else depth
                child_md = self._blocks_to_markdown(children, images_dir, child_depth)
                if child_md:
                    lines.append(child_md)
        
        return "\n\n".join(lines)
    
    def _block_to_markdown(self, block: dict, images_dir: Path, depth: int = 0) -> str:
        """Convert a single block to Markdown."""
        block_type = block.get("type")
        indent = "  " * depth
        
        if block_type == "paragraph":
            text = self._rich_text_to_markdown(block["paragraph"].get("rich_text", []))
            return text
        
        elif block_type == "heading_1":
            text = self._rich_text_to_markdown(block["heading_1"].get("rich_text", []))
            return f"# {text}"
        
        elif block_type == "heading_2":
            text = self._rich_text_to_markdown(block["heading_2"].get("rich_text", []))
            return f"## {text}"
        
        elif block_type == "heading_3":
            text = self._rich_text_to_markdown(block["heading_3"].get("rich_text", []))
            return f"### {text}"
        
        elif block_type == "bulleted_list_item":
            text = self._rich_text_to_markdown(block["bulleted_list_item"].get("rich_text", []))
            return f"{indent}- {text}"
        
        elif block_type == "numbered_list_item":
            text = self._rich_text_to_markdown(block["numbered_list_item"].get("rich_text", []))
            return f"{indent}1. {text}"
        
        elif block_type == "to_do":
            checked = "x" if block["to_do"].get("checked") else " "
            text = self._rich_text_to_markdown(block["to_do"].get("rich_text", []))
            return f"{indent}- [{checked}] {text}"
        
        elif block_type == "quote":
            text = self._rich_text_to_markdown(block["quote"].get("rich_text", []))
            return f"> {text}"
        
        elif block_type == "code":
            language = block["code"].get("language", "")
            code = self._extract_plain_text(block["code"].get("rich_text", []))
            return f"```{language}\n{code}\n```"
        
        elif block_type == "equation":
            expression = block["equation"].get("expression", "")
            if expression.strip():
                return f"$$\n{expression}\n$$"
        
        elif block_type == "image":
            return self._image_block_to_markdown(block["image"], images_dir)
        
        elif block_type == "bookmark":
            url = block["bookmark"].get("url", "")
            caption = self._extract_plain_text(block["bookmark"].get("caption", []))
            if caption:
                return f"[{caption}]({url})"
            return f"[{url}]({url})"
        
        elif block_type == "callout":
            icon = block["callout"].get("icon", {}).get("emoji", "")
            text = self._rich_text_to_markdown(block["callout"].get("rich_text", []))
            content = f"{icon} {text}" if icon else text
            return f"> {content}"
        
        elif block_type == "divider":
            return "---"
        
        elif block_type == "table":
            return self._table_to_markdown(block)
        
        return ""
    
    def _rich_text_to_markdown(self, rich_text: list) -> str:
        """Convert Notion rich text to Markdown."""
        parts = []
        
        for item in rich_text:
            if item.get("type") == "equation":
                expression = item.get("equation", {}).get("expression", "")
                if expression.strip():
                    parts.append(f"${expression}$")
                continue
            
            text = item.get("plain_text", "")
            if not text:
                continue
            
            annotations = item.get("annotations", {})
            
            # Apply formatting
            if annotations.get("bold"):
                text = f"**{text}**"
            if annotations.get("italic"):
                text = f"*{text}*"
            if annotations.get("strikethrough"):
                text = f"~~{text}~~"
            if annotations.get("underline"):
                text = f"<u>{text}</u>"
            if annotations.get("code"):
                text = f"`{text}`"
            
            # Apply link
            href = item.get("href")
            if href:
                text = f"[{text}]({href})"
            
            parts.append(text)
        
        return "".join(parts)
    
    def _image_block_to_markdown(self, image_block: dict, images_dir: Path) -> str:
        """Convert image block to Markdown with local image."""
        url = self._get_image_url(image_block)
        if not url:
            return ""
        
        # Download image
        self.image_counter += 1
        ext = self._get_extension(url)
        filename = f"image_{self.image_counter:03d}{ext}"
        local_path = images_dir / filename
        
        image_type = image_block.get("type", "external")
        
        if self._download_image(url, str(local_path)):
            self.images.append({
                "original_url": url,
                "local_path": str(local_path),
                "type": image_type
            })
            
            caption = self._extract_plain_text(image_block.get("caption", []))
            if caption:
                return f"![{caption}]({local_path})"
            return f"![]({local_path})"
        
        # Fallback to original URL if download fails
        caption = self._extract_plain_text(image_block.get("caption", []))
        if caption:
            return f"![{caption}]({url})"
        return f"![]({url})"
    
    def _table_to_markdown(self, table_block: dict) -> str:
        """Convert table block to Markdown."""
        rows = self._get_all_blocks(table_block["id"])
        
        if not rows:
            return "<!-- Empty table -->"
        
        md_rows = []
        
        for i, row in enumerate(rows):
            if row.get("type") != "table_row":
                continue
            
            cells = row["table_row"].get("cells", [])
            cell_texts = [
                self._rich_text_to_markdown(cell).replace("|", "\\|").replace("\n", "<br>")
                for cell in cells
            ]
            md_rows.append(f"| {' | '.join(cell_texts)} |")
            
            # Add header separator after first row
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                md_rows.append(separator)
        
        return "\n".join(md_rows)
    
    def _get_image_url(self, image_obj: dict) -> str:
        """Extract URL from Notion image object."""
        img_type = image_obj.get("type")
        
        if img_type == "external":
            return image_obj.get("external", {}).get("url", "")
        elif img_type == "file":
            return image_obj.get("file", {}).get("url", "")
        
        return ""
    
    def _get_extension(self, url: str) -> str:
        """Get file extension from URL."""
        # Remove query parameters
        clean_url = url.split("?")[0]
        
        # Try to get extension from URL
        if "." in clean_url:
            ext = os.path.splitext(clean_url)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
                return ext
        
        # Default to .png for Notion files
        if "amazonaws.com" in url or "notion" in url:
            return ".png"
        
        return ".jpg"
    
    def _download_image(self, url: str, local_path: str) -> bool:
        """Download image from URL to local path."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=30) as response:
                with open(local_path, "wb") as f:
                    f.write(response.read())
            
            return True
            
        except Exception as e:
            print(f"Warning: Failed to download image {url}: {e}", file=sys.stderr)
            return False
    
    def _extract_plain_text(self, rich_text: list) -> str:
        """Extract plain text from rich text array."""
        if not isinstance(rich_text, list):
            return ""
        return "".join(item.get("plain_text", "") for item in rich_text)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Notion article and convert to Markdown with images"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-id", help="Notion page ID")
    group.add_argument("--slug", help="Article slug (requires DATABASE_ID)")
    
    parser.add_argument(
        "--output-dir",
        default="/tmp/notion_article",
        help="Output directory for Markdown and images (default: /tmp/notion_article)"
    )
    
    parser.add_argument(
        "--notion-token",
        help="Notion integration token (or set NOTION_TOKEN env var or .env file)"
    )
    
    parser.add_argument(
        "--database-id",
        help="Notion database ID (or set DATABASE_ID env var or .env file)"
    )
    
    parser.add_argument(
        "--env-file",
        help="Path to .env file (default: auto-detect from cwd, home, or skill dir)"
    )
    
    args = parser.parse_args()
    
    # Load custom .env file if specified
    if args.env_file:
        env_path = Path(args.env_file)
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, _, value = line.partition("=")
                            key = key.strip()
                            value = value.strip()
                            if (value.startswith('"') and value.endswith('"')) or \
                               (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                            os.environ[key] = value  # Override existing
                print(f"Loaded environment from: {env_path}", file=sys.stderr)
            except Exception as e:
                print(f"Error loading {args.env_file}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: .env file not found: {args.env_file}", file=sys.stderr)
            sys.exit(1)
    
    # Get credentials (priority: CLI args > env vars > .env file)
    token = args.notion_token or os.environ.get("NOTION_TOKEN")
    if not token:
        print("Error: NOTION_TOKEN is required. Provide via --notion-token, NOTION_TOKEN env var, or .env file", file=sys.stderr)
        sys.exit(1)
    
    database_id = args.database_id or os.environ.get("DATABASE_ID")
    
    if args.slug and not database_id:
        print("Error: DATABASE_ID is required for slug lookup", file=sys.stderr)
        sys.exit(1)
    
    try:
        fetcher = NotionArticleFetcher(token, database_id)
        
        if args.page_id:
            result = fetcher.fetch_by_page_id(args.page_id, args.output_dir)
        else:
            result = fetcher.fetch_by_slug(args.slug, args.output_dir)
        
        # Output result as JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
