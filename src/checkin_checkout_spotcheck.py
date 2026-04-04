from pathlib import Path
import sys
from typing import Optional

import pandas as pd


ENRICHMENT_DIR = Path("outputs/enrichment")
SPOTCHECK_PATH = Path("data/qa/checkin_checkout_spotcheck_high.csv")


def get_first_file(folder: Path, pattern: str) -> Optional[Path]:
    files = sorted(folder.glob(pattern))
    return files[0] if files else None


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def main() -> None:
    if not SPOTCHECK_PATH.exists():
        print(f"Chýba spot-check fixture: {SPOTCHECK_PATH}")
        sys.exit(1)

    enrichment_path = get_first_file(ENRICHMENT_DIR, "*_enriched.csv")
    if enrichment_path is None:
        print("Chýba enrichment output pre spot-check.")
        sys.exit(1)

    expected_df = pd.read_csv(SPOTCHECK_PATH)
    actual_df = pd.read_csv(enrichment_path)

    merged = expected_df.merge(
        actual_df[
            [
                "hotel_name",
                "checkin_checkout_info",
                "checkin_checkout_status",
                "checkin_checkout_source_origin",
                "checkin_checkout_completeness",
            ]
        ],
        on="hotel_name",
        how="left",
        suffixes=("_expected", "_actual"),
    )

    merged["status"] = "PASS"
    for expected_column, actual_column in [
        ("expected_checkin_checkout_info", "checkin_checkout_info"),
        ("expected_checkin_checkout_status", "checkin_checkout_status"),
        ("expected_checkin_checkout_source_origin", "checkin_checkout_source_origin"),
        ("expected_checkin_checkout_completeness", "checkin_checkout_completeness"),
    ]:
        mismatch = (
            merged[expected_column].fillna("").astype(str).str.strip()
            != merged[actual_column].fillna("").astype(str).str.strip()
        )
        merged.loc[mismatch, "status"] = "FAIL"

    output_columns = [
        "hotel_name",
        "expected_checkin_checkout_info",
        "checkin_checkout_info",
        "expected_checkin_checkout_status",
        "checkin_checkout_status",
        "expected_checkin_checkout_source_origin",
        "checkin_checkout_source_origin",
        "expected_checkin_checkout_completeness",
        "checkin_checkout_completeness",
        "expected_review_note",
        "status",
    ]
    print(merged[output_columns].to_string(index=False))
    print(f"\nPočet case-ov: {len(merged)}")
    print(f"PASS: {(merged['status'] == 'PASS').sum()}")
    print(f"FAIL: {(merged['status'] == 'FAIL').sum()}")

    if (merged["status"] == "FAIL").any():
        sys.exit(1)


if __name__ == "__main__":
    main()
