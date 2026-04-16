with open("pipeline/02_write_chapters.py", "r", encoding="utf-8") as f:
    text2 = f.read()

text2 = text2.replace("import google.generativeai as genai", "from google import genai\\nfrom google.genai import types")

text2 = text2.replace("def expand_chunk(model,", "def expand_chunk(client, model_name,")
text2 = text2.replace("response = model.generate_content(prompt)", "response = client.models.generate_content(model=model_name, contents=prompt)")

text2 = text2.replace("def write_chapter_intro(model,", "def write_chapter_intro(client, model_name,")

text2 = text2.replace('genai.configure(api_key=os.environ["GEMINI_API_KEY"])', 'client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])')
text2 = text2.replace('model = genai.GenerativeModel(cfg["llm"]["model"])', 'model_name = cfg["llm"]["model"]')

text2 = text2.replace('intro = write_chapter_intro(model,', 'intro = write_chapter_intro(client, model_name,')
text2 = text2.replace('prose = expand_chunk(model,', 'prose = expand_chunk(client, model_name,')

with open("pipeline/02_write_chapters.py", "w", encoding="utf-8") as f:
    f.write(text2)

with open("pipeline/03_assemble_manuscript.py", "r", encoding="utf-8") as f:
    text3 = f.read()

text3 = text3.replace("import google.generativeai as genai", "from google import genai\\nfrom google.genai import types")

text3 = text3.replace('genai.configure(api_key=os.environ["GEMINI_API_KEY"])', 'client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])')
text3 = text3.replace('client = genai.GenerativeModel(cfg["llm"]["model"])', 'model_name = cfg["llm"]["model"]')

text3 = text3.replace("response = client.generate_content(", "response = client.models.generate_content(model=model_name, contents=")

with open("pipeline/03_assemble_manuscript.py", "w", encoding="utf-8") as f:
    f.write(text3)

with open("config.yaml", "r", encoding="utf-8") as f:
    cfg = f.read()

cfg = cfg.replace('model: "gemini-1.5-pro"', 'model: "gemini-2.0-flash"')

with open("config.yaml", "w", encoding="utf-8") as f:
    f.write(cfg)

print("Patch2 applied")
