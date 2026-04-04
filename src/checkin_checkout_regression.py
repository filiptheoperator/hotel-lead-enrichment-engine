from pathlib import Path
import sys

import pandas as pd

from enrich_hotels import (
    classify_checkin_checkout_completeness,
    extract_checkin_checkout_from_json_ld,
    extract_checkin_checkout_from_text,
    is_likely_checkin_checkout,
)


CASE_PATH = Path("data/qa/checkin_checkout_regression_cases.csv")


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_row(case: pd.Series) -> pd.Series:
    return pd.Series(
        {
            "hotel_name": normalize_text(case.get("hotel_name")),
            "category_name": normalize_text(case.get("category_name")),
            "all_categories": normalize_text(case.get("all_categories")),
        }
    )


def run_case(case: pd.Series) -> dict[str, str]:
    row = build_row(case)
    source_url = normalize_text(case.get("source_url"))
    input_text = normalize_text(case.get("input_text"))
    expected_value = normalize_text(case.get("expected_value"))
    expected_is_likely = normalize_text(case.get("expected_is_likely")).lower() == "yes"
    kind = normalize_text(case.get("kind"))

    if kind == "jsonld":
        html_payload = (
            '<script type="application/ld+json">'
            f"{input_text}"
            "</script>"
        )
        extracted_value = extract_checkin_checkout_from_json_ld(html_payload)
    else:
        extracted_value = extract_checkin_checkout_from_text(input_text)

    is_likely = is_likely_checkin_checkout(row, extracted_value, source_url) if extracted_value else False
    accepted_value = extracted_value if is_likely else ""
    value_ok = accepted_value == expected_value
    likely_ok = is_likely == expected_is_likely

    return {
        "case_id": normalize_text(case.get("case_id")),
        "kind": kind,
        "expected_value": expected_value,
        "actual_value": accepted_value,
        "actual_completeness": classify_checkin_checkout_completeness(accepted_value),
        "expected_is_likely": "yes" if expected_is_likely else "no",
        "actual_is_likely": "yes" if is_likely else "no",
        "status": "PASS" if value_ok and likely_ok else "FAIL",
    }


def main() -> None:
    if not CASE_PATH.exists():
        print(f"Chýba regression fixture: {CASE_PATH}")
        sys.exit(1)

    cases_df = pd.read_csv(CASE_PATH)
    results = [run_case(case) for _, case in cases_df.iterrows()]
    results_df = pd.DataFrame(results)

    print(results_df.to_string(index=False))

    failed_df = results_df[results_df["status"] != "PASS"]
    print(f"\nPočet case-ov: {len(results_df)}")
    print(f"PASS: {(results_df['status'] == 'PASS').sum()}")
    print(f"FAIL: {len(failed_df)}")

    if not failed_df.empty:
        sys.exit(1)


if __name__ == "__main__":
    main()
