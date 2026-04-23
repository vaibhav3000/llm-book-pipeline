# LLM Book Pipeline

> **Automated YouTube-to-eBook PDF pipeline powered by Large Language Models.**

Converts a YouTube playlist of educational lectures into a publication-quality PDF book - fetching transcripts, expanding them into polished prose with an LLM, assembling a full manuscript, and rendering a typeset PDF - all in Python, with no LaTeX dependency.

**Target Playlist:** [Building LLMs from Scratch – Dr. Raj Dander (VIUA)](https://www.youtube.com/watch?v=Xpr8D6LeAtw&list=PLPTV0NXA_ZSgsLAr8YCgCwhPIJNNtexWu)  
**Generated Output:** `output/Building_LLMs_from_Scratch.pdf`

---

## 📄 Technical Report

A comprehensive technical report documenting the full architecture, design decisions, algorithms, LLM integration strategy, prompt engineering, limitations, and future improvements is included in this repository:

| File | Description |
|------|-------------|
| [`Book_llm_pipeline_report.pdf`](./Book_llm_pipeline_report.pdf) | 📘 Full technical report (PDF) - **read this for a deep dive into how the pipeline works** |
| [`Book_llm_pipeline_report.tex`](./Book_llm_pipeline_report.tex) | LaTeX source of the report |

> **We strongly recommend going through the report** to understand the system architecture, prompt engineering methodology, chunking strategy, LLM backend comparison, and known limitations before running or extending the pipeline.

---

## Pipeline Architecture

The system is organized as a **linear four-stage pipeline**. Stages communicate exclusively through the filesystem, making each stage independently runnable and resumable.

```
YouTube Playlist
      │
      ▼
Stage 1: Fetch Transcripts       ──► cache/transcripts/*.json
      │                               (youtube-transcript-api + yt-dlp)
      ▼
Stage 2: Write Chapters (LLM)    ──► cache/chapters/*.md
      │                               (DeepSeek / Groq / Anthropic / Gemini)
      ▼
Stage 3: Assemble Manuscript     ──► output/manuscript.md
      │                               (foreword + TOC + chapters + glossary)
      ▼
Stage 4: Render PDF (ReportLab)  ──► output/Building_LLMs_from_Scratch.pdf
```

All LLM outputs are **file-cached by `video_id`** - re-runs skip already-processed videos. Any stage can be restarted independently.

---

## Repository Structure

```
llm-book-pipeline/
├── build_book.py                  # Entrypoint: orchestrates all 4 stages
├── config.yaml                    # All tunable parameters (model, chunk size, etc.)
├── requirements.txt               # Python dependencies
├── patch.py                       # Gemini API migration patch (v0.x)
├── patch2.py                      # Gemini v2 API migration patch (v1.x)
├── Book_llm_pipeline_report.pdf   # 📘 Technical report (READ THIS)
├── Book_llm_pipeline_report.tex   # LaTeX source of the report
├── pipeline/
│   ├── 01_fetch_transcripts.py    # Stage 1: fetch & clean YouTube transcripts
│   ├── 02_write_chapters.py       # Stage 2: LLM-powered prose expansion
│   ├── 03_assemble_manuscript.py  # Stage 3: foreword, TOC, glossary assembly
│   └── 04_render_pdf.py           # Stage 4: ReportLab PDF rendering
├── cache/
│   ├── video_index.json           # Playlist metadata
│   ├── transcripts/               # <video_id>.json per video
│   └── chapters/                  # <video_id>.md per video
├── output/
│   ├── manuscript.md              # Full assembled manuscript
│   └── Building_LLMs_from_Scratch.pdf
└── free_api_version/              # Groq (free-tier) variant — identical structure
    ├── build_book.py
    ├── config.yaml
    └── pipeline/
```

---

## Key Configuration (`config.yaml`)

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `llm.model` | `deepseek-chat` | LLM model identifier |
| `llm.chunk_size` | `3000` | Characters per transcript chunk |
| `llm.chunk_overlap` | `200` | Overlap between consecutive chunks |
| `llm.max_tokens` | `4096` | Max tokens in LLM response |
| `pipeline.force_refetch` | `false` | Override transcript cache |
| `pipeline.force_rewrite` | `false` | Override chapter cache |
| `pipeline.max_videos` | `null` | Limit videos (for testing) |

---

## Supported LLM Backends

| Backend | Model | Cost | Interface |
|---------|-------|------|-----------|
| **DeepSeek** | `deepseek-chat` | ~$0.10–0.20 (full 43 videos) | OpenAI-compatible |
| **Anthropic** | `claude-sonnet-4-*` | Higher | Native SDK |
| **Groq** | `llama-3.3-70b-versatile` | Free (rate-limited) | OpenAI-compatible |
| **Google Gemini** | `gemini-2.0-flash` | Low | Google GenAI SDK |

All four backends are supported via runtime config — no code changes needed.

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

```bash
# DeepSeek (default, cheapest — recommended)
export DEEPSEEK_API_KEY=sk-your-key-here          # Linux/Mac
$env:DEEPSEEK_API_KEY="sk-your-key-here"          # Windows PowerShell

# OR Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Run

**Quick test (5 videos):**
```bash
python build_book.py --max-videos 5
```

**Full 43-video playlist:**
```bash
python build_book.py
```

**Resume from a specific stage:**
```bash
python build_book.py --from 2     # resume from Stage 2
python build_book.py --only 4     # run only Stage 4 (PDF render)
python build_book.py --dry-run    # show plan without executing
```

---

## 🌟 Free API Version (Groq — No API Key Required)

A fully functional free variant is provided in `free_api_version/` using the Groq API (Llama 3.3-70B).

### Method A: Zero-Configuration (Preset Key)
```bash
cd free_api_version
python build_book.py
```

### Method B: Use Your Own Free Groq Key
1. Create a free account at [console.groq.com](https://console.groq.com/)
2. Set your key:
```bash
$env:GROQ_API_KEY="gsk_your_groq_key"   # Windows
export GROQ_API_KEY="gsk_your_groq_key" # Linux/Mac
```
3. Run:
```bash
python build_book.py --max-videos 5   # fast 5-video test
python build_book.py                  # full playlist
```

> [!WARNING]
> Running the full 43-video playlist on the free Groq tier will take many hours due to strict rate limits. The pipeline auto-pauses and resumes when limits are hit (no manual intervention needed), but expect it to run overnight. Use `--max-videos 5` for a fast end-to-end demo.

> [!NOTE]
> **Auto Rate-Limit Handling:** When the Groq free tier returns `Error 429`, the pipeline parses the exact cooldown duration from the error message and sleeps precisely that long before retrying — fully unattended.

---

## Design Highlights

| Principle | Implementation |
|-----------|----------------|
| **No hallucinations** | LLM strictly instructed to use only the provided transcript chunk |
| **Reproducible** | All LLM outputs cached to disk; re-runs produce identical results |
| **No LaTeX** | PDF rendered via ReportLab Platypus in pure Python |
| **Idempotent** | Each stage skips already-completed work; override with `force_refetch`/`force_rewrite` |
| **Multi-backend** | DeepSeek, Anthropic, Groq, and Gemini supported via one config change |
| **Cost-efficient** | ~$0.10–$0.20 USD for the full 43-video run on DeepSeek |

---

## Output

The pipeline produces:
- **43 transcript JSON files** in `cache/transcripts/` (~120,000 words of cleaned spoken content)  
- **Chapter Markdown files** in `cache/chapters/` (one per video)
- **`output/manuscript.md`** — full assembled manuscript
- **`output/Building_LLMs_from_Scratch.pdf`** — publication-quality PDF with cover page, TOC, foreword, 43 chapters, and a glossary (~200–350 pages, ~150,000–250,000 words)

---

## Requirements

- Python 3.10+
- DeepSeek / Anthropic / Groq / Gemini API key (Groq is free)
- Internet connection for Stage 1 (transcript fetching)

---

## Author

**Vaibhav Mahore**  
Indian Institute of Science, Bangalore — B.Tech, Mathematics and Computing

📘 *For full technical details, algorithms, prompt engineering methodology, and  architecture analysis — please read the [Technical Report](./Book_llm_pipeline_report.pdf).*
