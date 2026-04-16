import os

def patch_config():
    with open("config.yaml", "r") as f:
        content = f.read()
    content = content.replace('model: "claude-sonnet-4-20250514"', 'model: "gemini-1.5-pro"')
    with open("config.yaml", "w") as f:
        f.write(content)

def patch_02():
    with open("pipeline/02_write_chapters.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace top part
    top_replacement = """import os
import json
import time
import yaml
import google.generativeai as genai

SYSTEM_PROMPT = \"\"\"You are a technical book author writing a chapter of a book titled
"Building Large Language Models from Scratch". Your job is to take a raw YouTube
transcript excerpt and transform it into polished, book-quality prose.

RULES:
1. ONLY use information from the provided transcript. Do NOT add outside facts,
   numbers, or claims not present in the source material.
2. Write in clear, flowing prose - no bullet summaries. This is a book chapter,
   not a listicle.
3. Expand on the ideas: add clear transitions, explanations, examples that the
   speaker only implied. Make implicit reasoning explicit.
4. Preserve all technical accuracy. Never paraphrase code or equations loosely.
5. Write 400-600 words per transcript excerpt chunk.
6. Maintain a consistent tone: technical yet accessible, like a well-written
   O'Reilly book.
7. Do NOT start with "In this section" or "In this chapter". Just dive in.
\"\"\"

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if len(chunk) > 100:
            chunks.append(chunk)
        next_start = start + chunk_size - overlap
        if next_start <= start:
            break
        start = next_start
    return chunks

def expand_chunk(model, chunk: str, chapter_title: str,
                 chunk_idx: int, total_chunks: int) -> str:
    prompt = f\"\"\"{SYSTEM_PROMPT}

Chapter title: "{chapter_title}"
This is chunk {chunk_idx+1} of {total_chunks} from the transcript.

TRANSCRIPT EXCERPT:
{chunk}

Write this as flowing book prose. If this is the first chunk, you may write a
brief chapter-opening sentence. If it is a middle chunk, continue the narrative
naturally. If it is the last chunk, end with a paragraph that summarizes what
was covered and sets up the next chapter.\"\"\"
    response = model.generate_content(prompt)
    return response.text.strip()

def write_chapter_intro(model, title: str, full_text: str) -> str:
    preview = full_text[:2000]
    prompt = f\"\"\"Write a 2-3 sentence chapter introduction for a book chapter
titled "{title}". Base it ONLY on this transcript excerpt - no outside facts:

{preview}

Keep it concise, engaging, and technical. Do not start with "In this chapter".\"\"\"
    response = model.generate_content(prompt)
    return response.text.strip()

def run():"""
    
    # Find def run() to split the string
    run_idx = content.find("def run():")
    tail = content[run_idx + len("def run():"):]
    
    new_content = top_replacement + tail
    
    # Replace run block
    new_content = new_content.replace("""    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    model = cfg["llm"]["model"]""", """    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(cfg["llm"]["model"])""")

    new_content = new_content.replace("""intro = write_chapter_intro(client, v["title"], full_text, model)""", """intro = write_chapter_intro(model, v["title"], full_text)""")
    new_content = new_content.replace("""prose = expand_chunk(client, chunk, v["title"], i, len(chunks), model)""", """prose = expand_chunk(model, chunk, v["title"], i, len(chunks))""")
    
    with open("pipeline/02_write_chapters.py", "w", encoding="utf-8") as f:
        f.write(new_content)

def patch_03():
    with open("pipeline/03_assemble_manuscript.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace("import anthropic", "import google.generativeai as genai")
    content = content.replace("client = anthropic.Anthropic()", """genai.configure(api_key=os.environ["GEMINI_API_KEY"])\n    client = genai.GenerativeModel(cfg["llm"]["model"])""")
    
    # Foreword replacement
    old_foreword = """    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": f\"\"\"Write a Foreword for a technical book titled:
"{title}"

The book covers these chapters:
{chapter_list}

Write 3-4 paragraphs suitable for a foreword. Be technically enthusiastic but grounded.
Talk about why understanding LLMs from first principles matters. Do NOT fabricate author
names, dates, or specific claims. Keep it general and motivating.\"\"\"}]
    )
    return response.content[0].text.strip()"""
    
    new_foreword = """    response = client.generate_content(f\"\"\"Write a Foreword for a technical book titled:
"{title}"
The book covers these chapters:
{chapter_list}
Write 3-4 paragraphs suitable for a foreword. Be technically enthusiastic but grounded.
Talk about why understanding LLMs from first principles matters. Do NOT fabricate author
names, dates, or specific claims. Keep it general and motivating.\"\"\")
    return response.text.strip()"""
    
    content = content.replace(old_foreword, new_foreword)
    
    old_glossary = """    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": f\"\"\"Based on this technical content about LLMs,
produce a Glossary of 15-20 key terms. For each term, write a 1-2 sentence definition.
Format as:

**Term**: Definition.

Only define terms that appear in or are clearly implied by this content:

{sample}\"\"\"}]
    )
    return response.content[0].text.strip()"""
    
    new_glossary = """    response = client.generate_content(f\"\"\"Based on this technical content about LLMs,
produce a Glossary of 15-20 key terms. For each term, write a 1-2 sentence definition.
Format as:
**Term**: Definition.
Only define terms that appear in or are clearly implied by this content:
{sample}\"\"\")
    return response.text.strip()"""
    
    content = content.replace(old_glossary, new_glossary)
    
    with open("pipeline/03_assemble_manuscript.py", "w", encoding="utf-8") as f:
        f.write(content)

patch_config()
patch_02()
patch_03()
print("Patch applied.")
