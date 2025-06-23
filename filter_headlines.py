#!/usr/bin/env python3
"""
Filter headlines to remove automated/technical news that don't carry sentiment value.

This script processes headline JSON files from data/headlines_preds/ and saves
filtered versions to data/filtered_headlines/, removing administrative and
automated news that don't provide meaningful sentiment signals.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict


def is_automated_headline(text: str) -> bool:
    """
    Check if a headline matches patterns of automated/technical news.

    Args:
        text: The headline text to check

    Returns:
        True if the headline should be filtered out, False otherwise
    """

    # REMIT energy notifications
    if text.startswith("REMIT,"):
        return True

    # Trading window notifications
    if "Trading Window" in text:
        return True

    # Transaction in Own Shares
    if "Transaction in Own Shares" in text:
        return True

    # Board Meeting Intimations
    if "Board Meeting Intimation" in text:
        return True

    # Regulatory filing prefixes
    if text.startswith("REG-") or text.startswith("REG "):
        return True

    # UPDATE prefixes with numbers
    # if re.match(r"^UPDATE \d+", text):
    #     return True

    # # BRIEF prefixes
    # if text.startswith("BRIEF-"):
    #     return True

    # Company code patterns (6-digit numbers followed by " -")
    if re.search(r"\b\d{6}\s*-\s*", text):
        return True

    # Share buyback routine notifications
    if "share buyback" in text.lower():
        return True

    # Quarterly Trading Reports
    if "Quarterly Trading Report" in text:
        return True

    # Energy infrastructure patterns with Unavailable and MW
    if "Unavailable:" in text and "MW" in text:
        return True

    # # Timestamp patterns (DD.MM.YYYY HH:MM)
    # if re.search(r"\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}", text):
    #     return True

    # # Law firm investor alerts and investigations
    # if (
    #     text.startswith("INVESTOR ALERT:")
    #     or "Law Firm" in text
    #     or "Investigates Claims" in text
    # ):
    #     return True

    # # Daily market "factors to watch" summaries
    # if re.search(r"(stocks?\s*-\s*)?Factors to watch", text, re.IGNORECASE):
    #     return True

    # # Europe research roundoup
    # if text.startswith("EUROPE RESEARCH ROUNDUP"):
    #     return True

    # Monthly voting rights regulatory reports
    if "Information concerning the total number of voting rights and shares" in text:
        return True

    # # Monthly investor reports (technical bond/fund reports)
    # if re.search(r"Monthly Investor Report|SOL Lion.*investor report", text):
    #     return True

    # Fund management position changes (hedge fund trading activities)
    if re.search(
        r"(FUND MANAGEMENT|GLOBAL INVESTORS).*(TAKES|DISSOLVES|CUTS|RAISES).*SHARE STAKE",
        text,
    ):
        return True

    # Stock exchange short position reports
    if re.search(
        r"(TSX|CSE|NYSE|NASDAQ)\s*Short Positions\s*on\s*\d{4}/\d{2}/\d{2}", text
    ):
        return True

    # # News correction headlines
    # if text.startswith("CORRECTED-"):
    #     return True

    # RPT- (repeat) prefixed headlines
    if text.startswith("RPT-"):
        return True

    # Generic/vague short headlines (less than 3 words, no company specifics)
    words = text.strip().split()
    if len(words) <= 2 and not any(char.isdigit() for char in text):
        return True

    # Pure topic headers without content
    if text in ["MATERIAL LITIGATION", "BRAIN FREEZE"]:
        return True

    return False


def filter_headlines_file(input_file: Path, output_file: Path) -> Dict[str, int]:
    """
    Filter headlines from a single JSON file.

    Args:
        input_file: Path to input JSON file
        output_file: Path to output filtered JSON file

    Returns:
        Dictionary with filtering statistics
    """
    stats = {"total": 0, "filtered_out": 0, "kept": 0, "duplicates_removed": 0}

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            headlines = json.load(f)

        filtered_headlines = []
        filtered_sentiment = defaultdict(int)
        previous_text_lower = None

        for headline in headlines:
            stats["total"] += 1
            text = headline.get("text", "")
            text_lower = text.lower()
            sentiment = headline.get("label", "").lower()

            if (
                is_automated_headline(text)
                or headline.get("documentType", "") == "Filing"
                or headline.get("sourceName", "") == "Event Transcripts News"
            ):
                stats["filtered_out"] += 1
                filtered_sentiment[sentiment] += 1
            # Check for consecutive duplicate text (case-insensitive)
            elif text_lower == previous_text_lower:
                stats["duplicates_removed"] += 1
                stats["filtered_out"] += 1
                filtered_sentiment[sentiment] += 1
            else:
                filtered_headlines.append(headline)
                stats["kept"] += 1
                previous_text_lower = text_lower

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save filtered headlines
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(filtered_headlines, f, indent=2, ensure_ascii=False)

        print(f"Filtered sentiment counts: {dict(filtered_sentiment)}")

        # Add filtered sentiment counts to stats
        stats["filtered_sentiment"] = dict(filtered_sentiment)
        return stats

    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return stats


def main():
    """Main function to process all headline files."""

    # Paths
    input_dir = Path("data/headlines_preds")
    output_dir = Path("data/filtered_headlines")

    # Check if input directory exists
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return

    # Get all JSON files
    json_files = list(input_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return

    print(f"Found {len(json_files)} files to process")

    # Overall statistics
    total_stats = {
        "files_processed": 0,
        "total_headlines": 0,
        "total_filtered_out": 0,
        "total_kept": 0,
        "total_duplicates_removed": 0,
        "files_with_errors": 0,
        "total_filtered_sentiment": defaultdict(int),
    }

    # Process each file
    for input_file in sorted(json_files):
        print(f"Processing {input_file.name}...")

        # Create output filename (keep same name)
        output_file = output_dir / input_file.name

        # Filter the file
        file_stats = filter_headlines_file(input_file, output_file)

        if file_stats["total"] > 0:
            total_stats["files_processed"] += 1
            total_stats["total_headlines"] += file_stats["total"]
            total_stats["total_filtered_out"] += file_stats["filtered_out"]
            total_stats["total_kept"] += file_stats["kept"]
            total_stats["total_duplicates_removed"] += file_stats.get(
                "duplicates_removed", 0
            )

            # Aggregate filtered sentiment counts
            for sentiment, count in file_stats.get("filtered_sentiment", {}).items():
                total_stats["total_filtered_sentiment"][sentiment] += count

            # Print file statistics
            filter_pct = (file_stats["filtered_out"] / file_stats["total"]) * 100
            duplicates_info = ""
            if file_stats.get("duplicates_removed", 0) > 0:
                duplicates_info = f" (including {file_stats['duplicates_removed']:,} consecutive duplicates)"
            print(
                f"  Total: {file_stats['total']:,}, "
                f"Filtered out: {file_stats['filtered_out']:,} ({filter_pct:.1f}%){duplicates_info}, "
                f"Kept: {file_stats['kept']:,}"
            )
        else:
            total_stats["files_with_errors"] += 1

    # Print overall statistics
    print("\n" + "=" * 60)
    print("FILTERING SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files with errors: {total_stats['files_with_errors']}")
    print(f"Total headlines: {total_stats['total_headlines']:,}")
    print(f"Headlines filtered out: {total_stats['total_filtered_out']:,}")
    print(f"Headlines kept: {total_stats['total_kept']:,}")
    print(
        f"Consecutive duplicates removed: {total_stats['total_duplicates_removed']:,}"
    )

    if total_stats["total_filtered_sentiment"]:
        print("Filtered sentiment percentages:")
        total_filtered = sum(total_stats["total_filtered_sentiment"].values())
        for sentiment, count in total_stats["total_filtered_sentiment"].items():
            percentage = (count / total_filtered) * 100
            print(f"  {sentiment}: {count:,} ({percentage:.1f}%)")

    if total_stats["total_headlines"] > 0:
        overall_filter_pct = (
            total_stats["total_filtered_out"] / total_stats["total_headlines"]
        ) * 100
        duplicate_pct = (
            total_stats["total_duplicates_removed"] / total_stats["total_headlines"]
        ) * 100
        print(f"Overall filtering rate: {overall_filter_pct:.1f}%")
        print(f"Duplicate rate: {duplicate_pct:.1f}%")

    print(f"\nFiltered files saved to: {output_dir}")


if __name__ == "__main__":
    main()
