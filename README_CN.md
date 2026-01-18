# Notion to X Publisher Skill

从 Notion 获取文章并一键发布到 X（推特）长文。

[English](README.md) | [中文](README_CN.md)

---

> **⚠️ 依赖说明**
> 
> 本 Skill 依赖 [@wshuyi](https://github.com/wshuyi) 开发的 [x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill) 来实现 X Articles 发布流程和剪贴板操作。
> 
> 特别感谢 **wshuyi** 创建了优秀的 x-article-publisher skill，使得本项目的集成成为可能！🙏

---

## 解决的问题

将 Notion 内容发布到 X Articles 通常需要：
1. 从 Notion 复制内容
2. 格式全部丢失
3. 在 X 编辑器中手动重新格式化
4. 逐张上传图片
5. 正确定位图片位置

**这个 Skill 将整个过程自动化。**

---

## 功能特性

- **按 Slug 或 Page ID 获取**：灵活的文章查找方式
- **图片支持**：下载外部 URL 和 Notion 托管的图片
- **自动 Markdown 转换**：富文本、标题、列表、代码块
- **LaTeX 支持**：保留数学公式
- **一键发布**：整合获取和发布流程

---

## 系统要求

| 要求 | 说明 |
|------|------|
| Claude Code | [claude.ai/code](https://claude.ai/code) |
| Playwright MCP | 浏览器自动化 |
| X Premium Plus | Articles 功能需要高级订阅 |
| Python 3.9+ | 需安装以下依赖 |
| x-article-publisher | X 发布工作流 |

```bash
# 安装依赖
pip install notion-client Pillow

# macOS 额外依赖
pip install pyobjc-framework-Cocoa

# Windows 额外依赖
pip install pywin32 clip-util
```

---

## 安装方式

### 方式一：Git Clone

```bash
git clone https://github.com/your-username/notion-to-x-publisher-skill.git
cp -r notion-to-x-publisher-skill/skills/notion-to-x-publisher ~/.claude/skills/
```

### 方式二：手动复制

将 `notion-to-x-publisher` 文件夹复制到 `~/.claude/skills/`

---

## 配置

三种提供凭据的方式（按优先级排序）：

### 1. 命令行参数（最高优先级）
```bash
python fetch_notion_article.py --slug xxx --notion-token "secret_xxx" --database-id "abc123"
```

### 2. 环境变量
```bash
export NOTION_TOKEN="secret_xxx..."
export DATABASE_ID="abc123..."
```

### 3. .env 文件（自动加载）

在当前目录、`~/.env` 或 skill 目录创建 `.env` 文件：
```bash
NOTION_TOKEN=secret_xxx...
DATABASE_ID=abc123...
```

或指定路径：
```bash
python fetch_notion_article.py --slug xxx --env-file /path/to/.env
```

---

## 使用方法

### 自然语言

```
发布 Notion 文章 "my-article-slug" 到 X
```

```
把 Notion 页面 abc123 发布到推特长文
```

```
Publish my Notion article to X Articles: my-article-slug
```

### 手动步骤

```bash
# 步骤 1：从 Notion 获取
python ~/.claude/skills/notion-to-x-publisher/scripts/fetch_notion_article.py \
  --slug "my-article" \
  --output-dir /tmp/notion_article

# 步骤 2：解析为 X 格式（使用 x-article-publisher）
python ~/.claude/skills/x-article-publisher/scripts/parse_markdown.py \
  /tmp/notion_article/my-article.md

# 步骤 3：按 x-article-publisher 工作流发布
```

---

## 工作流程

```
Notion 页面
     ↓ fetch_notion_article.py
Markdown + 本地图片
     ↓ parse_markdown.py (x-article-publisher)
结构化数据（标题、图片、HTML）
     ↓ Playwright MCP
X Articles 编辑器
     ↓
草稿已保存
```

---

## 脚本参考

### fetch_notion_article.py

```bash
# 按 page ID
python fetch_notion_article.py --page-id <id>

# 按 slug
python fetch_notion_article.py --slug <slug>

# 自定义输出目录
python fetch_notion_article.py --slug <slug> --output-dir /path/to/output
```

**输出 JSON：**
```json
{
  "title": "文章标题",
  "slug": "article-slug",
  "markdown": "# 文章标题\n\n...",
  "markdown_file": "/tmp/notion_article/article.md",
  "images": [
    {"original_url": "...", "local_path": "...", "type": "external"}
  ],
  "cover_image": "/tmp/notion_article/images/cover.jpg"
}
```

---

## 数据库要求

使用 slug 查找时，Notion 数据库需要包含：

| 属性 | 类型 | 说明 |
|------|------|------|
| title | Title | 文章标题 |
| slug | Rich Text | URL 友好的标识符 |
| status | Select | 发布状态（不能是 "draft"） |

---

## 图片处理

### 支持的类型

1. **外部图片**：普通 URL（如 Unsplash、CDN）
2. **Notion 文件**：Notion 托管的图片（带签名 URL）

### 工作原理

1. 从 block 结构检测图片类型
2. 下载到本地 `images/` 文件夹
3. 将 Markdown 中的 URL 替换为本地路径
4. 封面图保存为 `cover.{ext}`

---

## 项目结构

```
notion-to-x-publisher/
├── SKILL.md              # Skill 指令
├── README.md             # 英文文档
├── README_CN.md          # 本文档
└── scripts/
    └── fetch_notion_article.py
```

---

## 依赖项目

本 Skill 依赖：
- **x-article-publisher**：提供 X 发布工作流和剪贴板脚本

确保 x-article-publisher 已安装在 `~/.claude/skills/x-article-publisher/`

---

## 故障排除

### "NOTION_TOKEN is required"
设置环境变量或使用 `--notion-token` 参数。

### "DATABASE_ID is required for slug lookup"
设置环境变量或使用 `--database-id` 参数。

### "Article with slug 'xxx' not found"
- 确认 slug 存在于数据库中
- 检查文章状态不是 "draft"
- 确保 Notion 集成有数据库访问权限

### 图片下载失败
- Notion 签名 URL 约 1 小时后过期
- 重新运行获取以获得新的 URL

---

## 许可证

MIT License

## 作者

配合 [x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill) 使用

---

## 贡献

- **Issues**：报告 bug 或请求功能
- **PRs**：欢迎！特别是 Windows 支持
