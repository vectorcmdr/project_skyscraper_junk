# project-skyscraper.com -- Local Mirror

Offline mirror of the Project Skyscraper ARG website. Fully
self-discovering: no hardcoded IDs or URL lists.

## Usage

```
.\update_mirror.ps1            # Update mirror from live site
.\update_mirror.ps1 -Serve     # Update then start local server
python serve_mirror.py         # Serve existing mirror on :8080
```

## What's Mirrored

- HTML pages (from sitemap + root)
- REST API (wp/v2, Jetpack, oEmbed, etc.)
- Media files (uploads, thumbnails)
- Theme assets (CSS, fonts)
- Plugin assets
- Discovery docs (sitemaps, robots.txt)
- Third-party CDN assets
- External references (Reddit, forums)

## Files

| File | Purpose |
|------|---------|
| `update_mirror.py` | Main update script (12 phases) |
| `update_mirror.ps1` | PowerShell wrapper |
| `serve_mirror.py` | Local HTTP server with URL rewriting |
| `MIRROR_MANIFEST.md` | Full file listing (auto-generated) |
| `POST_ID_SERIES.md` | Post/page/media ID analysis |
| `diffs/` | Change reports between runs |

## Key Features

- **Self-discovering** -- sitemap -> API -> HTML scanning -> derived
  assets. New posts, pages, media found automatically.
- **Idempotent** -- MD5 hash cache skips unchanged files.
- **Diffs** -- changed files listed in diffs/ after each run.
- **Offline browsing** -- serve_mirror.py rewrites all live URLs to
  local paths on-the-fly. No files modified.

## Stats

696 files, 22.9 MB (last run: 2026-05-27).
