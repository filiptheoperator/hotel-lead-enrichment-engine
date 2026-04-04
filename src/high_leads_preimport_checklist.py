from pathlib import Path

import pandas as pd


QA_DIR = Path("data/qa")
SHORTLIST_PATH = QA_DIR / "manual_review_shortlist.csv"
OUTPUT_CSV_PATH = QA_DIR / "high_leads_preimport_checklist.csv"
OUTPUT_TXT_PATH = QA_DIR / "high_leads_preimport_checklist.txt"


def load_shortlist() -> pd.DataFrame:
    if not SHORTLIST_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(SHORTLIST_PATH)


def build_high_leads_checklist() -> pd.DataFrame:
    shortlist_df = load_shortlist()
    if shortlist_df.empty:
        return pd.DataFrame(
            columns=[
                "hotel_name",
                "priority_score",
                "review_bucket",
                "operator_triage_action",
                "preimport_check_status",
            ]
        )

    high_df = shortlist_df[
        shortlist_df["priority_band"].fillna("").astype(str).str.strip().eq("High")
    ].copy()
    if high_df.empty:
        return pd.DataFrame(
            columns=[
                "hotel_name",
                "priority_score",
                "review_bucket",
                "operator_triage_action",
                "preimport_check_status",
            ]
        )

    hold_actions = {
        "hold_batch_due_to_dns_incident",
        "manual_review_before_clickup",
        "review_before_clickup",
    }
    high_df["preimport_check_status"] = high_df["operator_triage_action"].fillna("").astype(str).str.strip().map(
        lambda action: "BLOCKED" if action in hold_actions else "READY_FOR_REVIEW"
    )
    return high_df[
        [
            "hotel_name",
            "priority_score",
            "review_bucket",
            "operator_triage_action",
            "preimport_check_status",
        ]
    ].copy()


def save_high_leads_checklist(checklist_df: pd.DataFrame) -> tuple[Path, Path]:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    checklist_df.to_csv(OUTPUT_CSV_PATH, index=False)
    lines = [
        "High Leads Pre-Import Checklist",
        "",
        f"- rows: {len(checklist_df)}",
        f"- blocked_rows: {int(checklist_df.get('preimport_check_status', pd.Series(dtype='object')).eq('BLOCKED').sum()) if not checklist_df.empty else 0}",
    ]
    OUTPUT_TXT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return OUTPUT_CSV_PATH, OUTPUT_TXT_PATH


def main() -> None:
    checklist_df = build_high_leads_checklist()
    csv_path, txt_path = save_high_leads_checklist(checklist_df)
    print(f"High leads pre-import checklist uložený do: {csv_path}")
    print(f"High leads pre-import notes uložené do: {txt_path}")
    print("\nNáhľad:\n")
    if checklist_df.empty:
        print("Checklist je prázdny.")
    else:
        print(checklist_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
