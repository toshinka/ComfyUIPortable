#!/usr/bin/env python3
"""
Manga Tag Catalog Builder.

Converts an explicit local tag CSV (e.g., Danbooru tags export) into a compact,
deterministically sorted JSON catalog consumable by Manga's offline tag
autocomplete controller (manga/app/src/view/tag_autocomplete.js).

Contract:
- Reads quoted CSV safely with UTF-8 (and handles UTF-8 BOM).
- Identifies tag, category, and ranking/count columns.
- Strips whitespace, skips empty tags.
- Deduplicates deterministically, preserving the highest ranking.
- Sorts entries deterministically by (-ranking, tag).
- Outputs compact JSON array: [{"tag": "...", "category": "...", "ranking": N}, ...]
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

CATEGORY_ID_MAP = {
    "0": "general",
    "1": "artist",
    "3": "copyright",
    "4": "character",
    "5": "meta",
}


def find_column_name(header, candidates):
    header_lower_map = {col.strip().lower(): col for col in header if col}
    for candidate in candidates:
        if candidate.lower() in header_lower_map:
            return header_lower_map[candidate.lower()]
    return None


def parse_ranking(value, fallback=0):
    if value is None:
        return fallback
    val_str = str(value).strip()
    if not val_str:
        return fallback
    try:
        return int(val_str)
    except ValueError:
        try:
            return int(float(val_str))
        except ValueError:
            return fallback


def normalize_category(value):
    if value is None:
        return ""
    val_str = str(value).strip().lower()
    if val_str in CATEGORY_ID_MAP:
        return CATEGORY_ID_MAP[val_str]
    return val_str


def build_catalog_from_csv(
    input_csv_path,
    tag_col=None,
    category_col=None,
    ranking_col=None
):
    input_path = Path(input_csv_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input CSV file not found: {input_path}")

    # Read with utf-8-sig to automatically handle any BOM
    with open(input_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"CSV file is empty: {input_path}")

        actual_tag_col = tag_col or find_column_name(header, ["TAG", "tag", "name"])
        if not actual_tag_col:
            raise ValueError(
                f"Could not identify tag column in header: {header}. "
                "Specify explicitly with --tag-col."
            )
        try:
            tag_idx = header.index(actual_tag_col)
        except ValueError:
            raise ValueError(f"Tag column '{actual_tag_col}' not found in header {header}")

        actual_cat_col = category_col or find_column_name(header, ["CATEGORY", "category", "type"])
        cat_idx = header.index(actual_cat_col) if actual_cat_col in header else -1

        actual_rank_col = ranking_col or find_column_name(
            header, ["RANKING", "ranking", "count", "post_count", "posts"]
        )
        rank_idx = header.index(actual_rank_col) if actual_rank_col in header else -1

        entries_by_tag = {}
        total_rows = 0
        skipped_empty = 0

        for row in reader:
            total_rows += 1
            if not row or tag_idx >= len(row):
                skipped_empty += 1
                continue

            raw_tag = row[tag_idx].strip()
            if not raw_tag:
                skipped_empty += 1
                continue

            raw_category = row[cat_idx].strip() if (cat_idx >= 0 and cat_idx < len(row)) else ""
            category = normalize_category(raw_category)

            raw_ranking = row[rank_idx].strip() if (rank_idx >= 0 and rank_idx < len(row)) else "0"
            ranking = parse_ranking(raw_ranking, 0)

            if raw_tag in entries_by_tag:
                existing = entries_by_tag[raw_tag]
                # Keep the entry with highest ranking
                if ranking > existing["ranking"]:
                    entries_by_tag[raw_tag] = {
                        "tag": raw_tag,
                        "category": category or existing["category"],
                        "ranking": ranking
                    }
                elif not existing["category"] and category:
                    existing["category"] = category
            else:
                entries_by_tag[raw_tag] = {
                    "tag": raw_tag,
                    "category": category,
                    "ranking": ranking
                }

    # Deterministic sort: descending ranking, then ascending alphabetical tag
    sorted_entries = sorted(
        entries_by_tag.values(),
        key=lambda e: (-e["ranking"], e["tag"])
    )

    stats = {
        "input_file": str(input_path.resolve()),
        "total_rows_read": total_rows,
        "skipped_empty": skipped_empty,
        "unique_tags": len(sorted_entries),
        "tag_col": actual_tag_col,
        "category_col": actual_cat_col,
        "ranking_col": actual_rank_col,
    }
    return sorted_entries, stats


def write_catalog_json(entries, output_json_path):
    out_path = Path(output_json_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))

    return out_path.stat().st_size


def default_output_path():
    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "manga" / "app" / "data" / "danbooru_tags.json"


def main():
    parser = argparse.ArgumentParser(
        description="Build Manga Danbooru tag catalog JSON from a local CSV."
    )
    parser.add_argument(
        "input_csv",
        help="Path to local source CSV file."
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Target output JSON path (defaults to manga/app/data/danbooru_tags.json)."
    )
    parser.add_argument(
        "--tag-col",
        default=None,
        help="Name of tag column (auto-detected if omitted)."
    )
    parser.add_argument(
        "--category-col",
        default=None,
        help="Name of category column (auto-detected if omitted)."
    )
    parser.add_argument(
        "--ranking-col",
        default=None,
        help="Name of ranking column (auto-detected if omitted)."
    )

    args = parser.parse_args()

    output_path = Path(args.output) if args.output else default_output_path()

    print(f"Building tag catalog from: {args.input_csv}")
    try:
        entries, stats = build_catalog_from_csv(
            args.input_csv,
            tag_col=args.tag_col,
            category_col=args.category_col,
            ranking_col=args.ranking_col
        )
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        return 1

    file_size = write_catalog_json(entries, output_path)
    stats["output_file"] = str(output_path.resolve())
    stats["file_size_bytes"] = file_size
    stats["file_size_mb"] = round(file_size / (1024 * 1024), 2)

    print(f"Successfully generated catalog: {output_path}")
    print(f"  Rows read:     {stats['total_rows_read']}")
    print(f"  Skipped empty: {stats['skipped_empty']}")
    print(f"  Unique tags:   {stats['unique_tags']}")
    print(f"  Output size:   {stats['file_size_bytes']} bytes ({stats['file_size_mb']} MB)")
    print(f"  Columns: tag='{stats['tag_col']}', category='{stats['category_col']}', ranking='{stats['ranking_col']}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
