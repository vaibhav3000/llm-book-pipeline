"""
pipeline/01_fetch_transcripts.py
Fetches transcripts for all videos in the playlist.
Saves each transcript to cache/transcripts/<video_id>.json
"""

import os
import json
import time
import yaml
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def get_playlist_videos(playlist_id: str) -> list[dict]:
    """Fetch all video IDs and titles from a YouTube playlist."""
    print(f"Fetching playlist metadata for: {playlist_id}")
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "playlist_items": "1-200",
    }
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = info.get("entries", [])
        videos = [{"id": e["id"], "title": e["title"], "index": i+1}
                  for i, e in enumerate(entries) if e.get("id")]
    print(f"Found {len(videos)} videos in playlist")
    return videos

def fetch_transcript(video_id: str) -> list[dict] | None:
    """Fetch transcript for a single video. Returns list of {text, start, duration}."""
    api = YouTubeTranscriptApi()
    try:
        transcript = api.fetch(video_id)
        return [{"text": seg.text, "start": seg.start, "duration": seg.duration}
                for seg in transcript]
    except Exception as e:
        print(f"  WARNING: Could not fetch transcript for {video_id}: {e}")
        return None

def clean_transcript(segments: list[dict]) -> str:
    """Join segments, fix line breaks, strip artifacts."""
    raw = " ".join(seg["text"] for seg in segments)
    # Remove music/noise annotations
    import re
    raw = re.sub(r'\[.*?\]', '', raw)
    raw = re.sub(r'\(.*?\)', '', raw)
    # Collapse whitespace
    raw = re.sub(r'\s+', ' ', raw).strip()
    return raw

def run():
    cfg = load_config()
    os.makedirs(cfg["paths"]["transcripts_dir"], exist_ok=True)
    force = cfg["pipeline"]["force_refetch"]
    max_v = cfg["pipeline"]["max_videos"]

    # Step 1: get video list
    videos = get_playlist_videos(cfg["playlist"]["id"])
    if max_v:
        videos = videos[:max_v]

    # Save video index
    index_path = os.path.join(cfg["paths"]["cache_dir"], "video_index.json")
    with open(index_path, "w") as f:
        json.dump(videos, f, indent=2)
    print(f"Saved video index → {index_path}")

    # Step 2: fetch transcripts
    success, skipped, failed = 0, 0, 0
    for v in videos:
        out_path = os.path.join(cfg["paths"]["transcripts_dir"], f"{v['id']}.json")
        if os.path.exists(out_path) and not force:
            print(f"  [{v['index']:02d}] CACHED  {v['title'][:60]}")
            skipped += 1
            continue

        print(f"  [{v['index']:02d}] Fetching {v['title'][:60]} ...")
        segments = fetch_transcript(v["id"])
        if segments is None:
            failed += 1
            continue

        cleaned = clean_transcript(segments)
        data = {
            "video_id": v["id"],
            "title": v["title"],
            "index": v["index"],
            "raw_segments": segments,
            "cleaned_text": cleaned,
            "word_count": len(cleaned.split()),
        }
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"         → {data['word_count']} words saved")
        success += 1
        time.sleep(0.5)  # polite rate limiting

    print(f"\n✓ Done. Success: {success}, Cached: {skipped}, Failed: {failed}")

if __name__ == "__main__":
    run()
