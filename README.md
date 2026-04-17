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

### 🌟 Free API Version (Groq Llama 3)
If you don't have paid API keys (or just want a 1-click end-to-end test), a fully functional pipeline is provided out-of-the-box in the `free_api_version` directory.

#### Method A: 1-Click Zero-Configuration (Preset Key)
This version allows you to run the pipeline exactly as submitted without signing up for any services:
**Step 1:** Enter the free version directory
```bash
cd free_api_version
```
**Step 2:** Start the pipeline entirely for free
```bash
python build_book.py
```

#### Method B: Use Your Own Free Key
If you prefer to securely use your own free Groq API key:
**Step 1:** Create an account at [Groq Console](https://console.groq.com/) and generate a free API key.
**Step 2:** Enter the directory and set your API key
```bash
cd free_api_version

# Windows PowerShell:
$env:GROQ_API_KEY="gsk_your_groq_key"

# Linux / Mac:
export GROQ_API_KEY="gsk_your_groq_key"
```
**Step 3:** Run the pipeline

To safely test the pipeline blazing-fast (processing exactly 5 videos instead of the entire playlist):
```bash
python build_book.py --max-videos 5
```

If you want to compile the absolutely massive, full out-of-the-box 43-video playbook, simply run:
```bash
python build_book.py
```

> [!WARNING]
> Do NOT run the completely massive 43-video playlist using the Free API Version unless you have an exponential amount of time. Because the free Groq Limits heavily throttle execution, processing all 45 video chapters using exclusively free tokens will iteratively pause/resume and ultimately require leaving your computer running for dozens of hours in the background gracefully. If you want to review the execution seamlessly, absolutely use the `python build_book.py --max-videos 5` command!

> [!NOTE]
> **Dealing with Free API Limits:** Because the pipeline expands a huge playlist, the free Groq API will inevitably hit its strict free tier limits (`Error 429: rate_limit_exceeded`) midway through the build. This is totally normal! The pipeline actually features an advanced auto-retry mechanism configured specifically for this scenario. Whenever a limit is hit, the script automatically pauses itself (sometimes for ~1 hour depending on your daily tokens), perfectly calculates the required wait time, and flawlessly resumes building exactly where it left off the second your limits natively renew. Absolutely no manual intervention is required! *(Note: If you run the pipeline using a paid API key like Anthropic or DeepSeek, you will not hit these limits and the full execution will stream through completely uninterrupted!)*

---

## Run

**Test run (5 videos fast execution):**
```bash
python build_book.py --max-videos 5
```

**Full playlist execution (43+ videos):**
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
├── free_api_version/          # Alternative pre-configured to use free Groq API
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
