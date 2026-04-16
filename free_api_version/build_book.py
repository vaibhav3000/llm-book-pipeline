#!/usr/bin/env python3
"""
build_book.py — Single entrypoint for the full pipeline.

Usage:
  python build_book.py              # Run all stages
  python build_book.py --from 2     # Start from stage 2
  python build_book.py --only 4     # Run only stage 4
  python build_book.py --dry-run    # Print plan without executing

Stages:
  1 — Fetch transcripts from YouTube
  2 — Write chapters via Claude API
  3 — Assemble manuscript markdown
  4 — Render PDF
"""

import sys
import os
import time
import argparse

STAGES = {
    1: ("Fetch transcripts",    "pipeline/01_fetch_transcripts.py"),
    2: ("Write chapters (LLM)", "pipeline/02_write_chapters.py"),
    3: ("Assemble manuscript",  "pipeline/03_assemble_manuscript.py"),
    4: ("Render PDF",           "pipeline/04_render_pdf.py"),
}

def check_env():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)
    print(f"✓ ANTHROPIC_API_KEY found (sk-ant-...{key[-6:]})")

def run_stage(stage_num: int, dry_run: bool = False):
    name, script = STAGES[stage_num]
    print(f"\n{'='*60}")
    print(f"  Stage {stage_num}: {name}")
    print(f"{'='*60}")
    if dry_run:
        print(f"  [dry-run] would execute: python {script}")
        return
    t0 = time.time()
    ret = os.system(f"python {script}")
    elapsed = time.time() - t0
    if ret != 0:
        print(f"\nERROR: Stage {stage_num} failed (exit code {ret})")
        sys.exit(ret)
    print(f"\n  Stage {stage_num} done in {elapsed:.1f}s")

def main():
    parser = argparse.ArgumentParser(description="Build LLM book from YouTube playlist")
    parser.add_argument("--from",   dest="from_stage", type=int, default=1,
                        help="Start from stage N (default: 1)")
    parser.add_argument("--only",   dest="only_stage", type=int, default=None,
                        help="Run only stage N")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print plan without executing")
    args = parser.parse_args()

    print("=" * 58)
    print("  Building LLMs from Scratch - Book Pipeline")
    print("=" * 58)

    if not args.dry_run:
        pass # check_env() disabled because API key is hardcoded in script

    if args.only_stage:
        stages_to_run = [args.only_stage]
    else:
        stages_to_run = [s for s in STAGES if s >= args.from_stage]

    print(f"\nStages to run: {stages_to_run}")
    t_total = time.time()

    for s in stages_to_run:
        run_stage(s, dry_run=args.dry_run)

    elapsed = time.time() - t_total
    print(f"\n{'='*60}")
    print(f"  All stages complete in {elapsed/60:.1f} minutes")
    print(f"  Output: output/Building_LLMs_from_Scratch.pdf")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
