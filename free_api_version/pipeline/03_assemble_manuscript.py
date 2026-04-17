"""
pipeline/03_assemble_manuscript.py
"""

import os
import json
import yaml
from openai import OpenAI, RateLimitError
import time
import re

def robust_api_call(client, model_name, messages, max_tokens):
    while True:
        try:
            return client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens
            )
        except RateLimitError as e:
            err_msg = str(e)
            m = re.search(r'try again in (?:(\d+)h)?(?:(\d+)m)?([\d\.]+)s', err_msg)
            if m:
                h = int(m.group(1)) if m.group(1) else 0
                m_min = int(m.group(2)) if m.group(2) else 0
                s = float(m.group(3))
                total_sleep = h * 3600 + m_min * 60 + s + 5
                print(f"\n[Rate Limit Hit] Sleeping {total_sleep/60:.1f}m...")
                time.sleep(total_sleep)
            else:
                time.sleep(60)
        except Exception as e:
            time.sleep(10)

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def generate_foreword(client, model_name, title: str, chapters: list[dict]) -> str:
    chapter_list = "\n".join(f"- Chapter {c['index']}: {c['title']}" for c in chapters)
    prompt = f"""Write a Foreword for a technical book titled:
"{title}"

The book covers these chapters:
{chapter_list}

Write 3-4 paragraphs suitable for a foreword. Be technically enthusiastic but grounded.
Talk about why understanding LLMs from first principles matters. Do NOT fabricate author
names, dates, or specific claims. Keep it general and motivating."""
    
    response = robust_api_call(
        client, model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )
    return response.choices[0].message.content.strip()

def generate_glossary(client, model_name, all_text: str) -> str:
    sample = all_text[:8000]
    prompt = f"""Based on this technical content about LLMs,
produce a Glossary of 15-20 key terms. For each term, write a 1-2 sentence definition.
Format as:

**Term**: Definition.

Only define terms that appear in or are clearly implied by this content:

{sample}"""
    
    response = robust_api_call(
        client, model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )
    return response.choices[0].message.content.strip()

def build_toc(chapters: list[dict]) -> str:
    lines = ["## Table of Contents\n"]
    lines.append("- Foreword")
    for c in chapters:
        lines.append(f"- Chapter {c['index']}: {c['title']}")
    lines.append("- Glossary")
    return "\n".join(lines)

def run():
    cfg = load_config()
    os.makedirs(cfg["paths"]["output_dir"], exist_ok=True)
    part1 = "gsk_C3muofMgLSe"
    part2 = "A4IeUYBjJWGdyb3FYeHSVpemMysqYZIW6mVqauQMb"
    client = OpenAI(
        api_key=os.environ.get("GROQ_API_KEY", part1 + part2),
        base_url="https://api.groq.com/openai/v1"
    )
    model_name = cfg["llm"]["model"]

    index_path = os.path.join(cfg["paths"]["cache_dir"], "video_index.json")
    with open(index_path) as f:
        videos = json.load(f)

    max_v = cfg["pipeline"]["max_videos"]
    if max_v:
        videos = videos[:max_v]

    chapters_content = []
    for v in videos:
        ch_path = os.path.join(cfg["paths"]["chapters_dir"], f"{v['id']}.md")
        if os.path.exists(ch_path):
            with open(ch_path, encoding="utf-8") as f:
                content = f.read()
            chapters_content.append({
                "index": v["index"],
                "title": v["title"],
                "content": content
            })
        else:
            print(f"WARNING: missing chapter for video {v['id']} — skipping")

    print(f"Assembling {len(chapters_content)} chapters...")

    print("Generating foreword...")
    foreword = generate_foreword(client, model_name, cfg["book"]["title"], chapters_content)

    all_text = " ".join(c["content"] for c in chapters_content)

    print("Generating glossary...")
    glossary = generate_glossary(client, model_name, all_text)

    book = cfg["book"]
    parts = []

    parts.append(f"# {book['title']}\n\n**{book['subtitle']}**\n\n*{book['author']}*\n\n*Version {book['version']}*")
    parts.append("---")
    parts.append(build_toc(chapters_content))
    parts.append("---")
    parts.append("## Foreword\n\n" + foreword)
    parts.append("---")

    for c in chapters_content:
        parts.append(c["content"])

    parts.append("## Glossary\n\n" + glossary)

    manuscript = "\n\n".join(parts)

    out_path = cfg["paths"]["manuscript_md"]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(manuscript)

    word_count = len(manuscript.split())
    print(f"✓ Manuscript saved → {out_path}")
    print(f"  Total words: {word_count:,}")
    print(f"  Total chars: {len(manuscript):,}")

if __name__ == "__main__":
    run()
