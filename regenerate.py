#!/usr/bin/env python3
"""Convert DictArabic.csv to the extension dictionary JSON."""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "database" / "DictArabic.csv"
OUTPUT_PATH = ROOT / "database" / "dictionary.json"

COL_WRONG = "الكتابة الخاطئة"
COL_CORRECT = "الكتابة الصحيحة"
COL_DIACRITICS = "التشكيل"
COL_REASON = "السبب"


def word_count(text: str) -> int:
    return len(text.split())


def convert(csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    required = {COL_WRONG, COL_CORRECT}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise SystemExit(
            f"Unexpected CSV headers: {reader.fieldnames!r}. "
            f"Expected at least {sorted(required)}"
        )

    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    max_phrase_words = 1
    skipped = 0

    for row in reader:
        wrong = (row.get(COL_WRONG) or "").strip()
        correct = (row.get(COL_CORRECT) or "").strip()
        diacritics = (row.get(COL_DIACRITICS) or "").strip()
        reason = (row.get(COL_REASON) or "").strip()

        if not wrong or not correct:
            skipped += 1
            continue

        max_phrase_words = max(max_phrase_words, word_count(wrong))
        correction = {
            "plain": correct,
            "diacritics": diacritics,
            "reason": reason,
        }

        if wrong not in grouped:
            grouped[wrong] = []

        if correction not in grouped[wrong]:
            grouped[wrong].append(correction)

    entries = {
        wrong: {"corrections": corrections}
        for wrong, corrections in grouped.items()
    }

    return {
        "version": 1,
        "source": str(CSV_PATH.relative_to(ROOT)),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "maxPhraseWords": max_phrase_words,
        "entryCount": len(entries),
        "entries": entries,
        "_meta": {"skippedRows": skipped},
    }


def main() -> int:
    if not CSV_PATH.is_file():
        raise SystemExit(f"CSV not found: {CSV_PATH}")

    print(f"Reading {CSV_PATH}")
    csv_text = CSV_PATH.read_text(encoding="utf-8-sig")
    data = convert(csv_text)

    # Drop build-only meta from the shipped file
    skipped = data.pop("_meta", {}).get("skippedRows", 0)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Wrote {data['entryCount']} entries "
        f"(max phrase words: {data['maxPhraseWords']}, skipped rows: {skipped}) "
        f"-> {OUTPUT_PATH}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
