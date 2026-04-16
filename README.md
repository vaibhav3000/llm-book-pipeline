# Building Large Language Models from Scratch

A reproducible pipeline that converts the YouTube playlist
"Building LLMs from Scratch" into an eBook-quality PDF manuscript
using LLMs for content expansion.

**Playlist:**
https://www.youtube.com/watch?v=Xpr8D6LeAtw&list=PLPTV0NXA_ZSgsLAr8YCgCwhPIJNNtexWu

**Generated PDF:** `output/Building_LLMs_from_Scratch.pdf`

---

## Pipeline Architecture

```
YouTube Playlist
      |
      v
Stage 1: Fetch Transcripts       (youtube-transcript-api + yt-dlp)
      |
      v
Stage 2: Write Chapters          (DeepSeek API - prose expansion per chunk)
      |
      v
Stage 3: Assemble Manuscript     (foreword + TOC + chapters + glossary)
      |
      v
Stage 4: Render PDF              (ReportLab - no LaTeX dependency)
      |
      v
output/Building_LLMs_from_Scratch.pdf
```

Each stage writes to disk. The pipeline is fully resumable from any stage.
All LLM outputs are cached to `cache/` so re-runs do not repeat API calls.

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/vaibhav3000/llm-book-pipeline.git
cd llm-book-pipeline
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set your API key**

The pipeline uses DeepSeek by default (cheapest, OpenAI-compatible).
Get a key at https://platform.deepseek.com

```bash
# Linux / Mac
export DEEPSEEK_API_KEY=sk-your-key-here

# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-your-key-here"
```

To use Anthropic Claude instead, update `config.yaml` model to
`claude-sonnet-4-20250514` and set `ANTHROPIC_API_KEY`.

---

## Run

**Test run (3 videos, costs under $0.05):**

Set `max_videos: 3` in `config.yaml`, then:
```bash
python build_book.py
```

**Full playlist:**

Set `max_videos: null` in `config.yaml`, then:
```bash
python build_book.py
```

**Resume from a specific stage:**
```bash
python build_book.py --from 2
python build_book.py --only 4
python build_book.py --dry-run
```

---

## Repo Structure

```
repo/
├── build_book.py              # Single entrypoint - runs all stages
├── config.yaml                # Playlist URL, model params, output paths
├── requirements.txt           # All dependencies
├── README.md
├── pipeline/
│   ├── 01_fetch_transcripts.py   # Fetch + clean YouTube transcripts
│   ├── 02_write_chapters.py      # Expand transcripts into book prose
│   ├── 03_assemble_manuscript.py # Foreword, TOC, glossary assembly
│   └── 04_render_pdf.py          # ReportLab PDF rendering
├── cache/
│   ├── video_index.json          # Playlist metadata
│   ├── transcripts/              # Per-video cleaned transcripts
│   └── chapters/                 # Per-video generated chapters
└── output/
    ├── manuscript.md             # Full assembled manuscript
    └── Building_LLMs_from_Scratch.pdf
```

---

## Design Decisions

**No hallucinations:** Claude/DeepSeek is instructed to only use content
from the provided transcript chunk. No outside knowledge injection.

**Reproducible:** All LLM outputs cached as JSON. Re-running the pipeline
with the same transcripts produces the same book.

**No LaTeX dependency:** PDF rendered directly via ReportLab in pure Python.
Works on any OS without a TeX installation.

**Idempotent stages:** Each stage checks for existing output before running.
Set `force_refetch: true` or `force_rewrite: true` in `config.yaml` to override.

---

## Requirements

- Python 3.10+
- DeepSeek API key (or Anthropic API key)
- Internet connection for Stage 1
