from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_DIR = Path("outputs/enrichment")
CLICKUP_DIR = Path("outputs/clickup")
QA_DIR = Path("data/qa")
QA_CONFIG_PATH = Path("configs/qa.yaml")
MANUAL_REVIEW_SHORTLIST_PATH = QA_DIR / "manual_review_shortlist.csv"
CLICKUP_REQUIRED_COLUMNS = ["Task name"]
CLICKUP_SUPPORTED_CORE_COLUMNS = [
    "Task name",
    "Description content",
    "Status",
    "Priority",
]


def get_first_file(folder: Path, pattern: str) -> Optional[Path]:
    files = sorted(folder.glob(pattern))
    return files[0] if files else None


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_csv(file_path: Optional[Path]) -> pd.DataFrame:
    if file_path is None:
        return pd.DataFrame()
    return pd.read_csv(file_path)


def load_qa_config(config_path: Path = QA_CONFIG_PATH) -> dict:
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def normalize_severity(value: str) -> str:
    normalized = normalize_text(value)
    return normalized if normalized else "Info"


def is_dns_fetch_blocked(row: pd.Series) -> bool:
    fetch_status = normalize_text(row.get("public_source_fetch_status"))
    return fetch_status in {"dns_resolution_failed", "dns_resolution_failed_fallback_previous"}


def is_single_side_verified_checkin_checkout(row: pd.Series) -> bool:
    return (
        normalize_text(row.get("checkin_checkout_status")) == "Overené vo verejnom zdroji"
        and normalize_text(row.get("checkin_checkout_completeness")) == "single_side"
    )


def build_issue(
    issue_type: str,
    severity: str,
    hotel_name: object,
    city: object,
    priority_band: object,
    details: str,
    source_file: object,
) -> dict[str, object]:
    return {
        "issue_type": issue_type,
        "severity": normalize_severity(severity),
        "blocking": "yes" if normalize_severity(severity) == "High" else "no",
        "hotel_name": normalize_text(hotel_name),
        "city": normalize_text(city),
        "priority_band": normalize_text(priority_band),
        "details": details,
        "source_file": normalize_text(source_file),
    }


def normalize_clickup_priority_value(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    try:
        number = int(float(text))
    except ValueError:
        return text
    return str(number)


def has_clickup_required_columns(clickup_df: pd.DataFrame) -> tuple[bool, list[str]]:
    missing_columns = [column for column in CLICKUP_REQUIRED_COLUMNS if column not in clickup_df.columns]
    return (len(missing_columns) == 0, missing_columns)


def build_issue_rows(
    processed_df: pd.DataFrame,
    enrichment_df: pd.DataFrame,
    clickup_df: pd.DataFrame,
) -> pd.DataFrame:
    issues: list[dict[str, object]] = []
    qa_config = load_qa_config().get("qa", {})
    single_side_high_priority_score_threshold = float(
        qa_config.get("single_side_high_priority_score_threshold", 9.0)
    )
    public_web_fetch_incident_threshold_share = float(
        qa_config.get("public_web_fetch_incident_threshold_share", 0.5)
    )

    if not processed_df.empty:
        duplicate_mask = processed_df.duplicated(
            subset=["hotel_name", "city", "street"], keep=False
        )
        for _, row in processed_df[duplicate_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="duplicate_lead",
                    severity="High",
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Duplicitný lead podľa hotel_name + city + street.",
                    source_file=row.get("source_file"),
                )
            )

        missing_contact_mask = (
            processed_df["website"].fillna("").astype(str).str.strip().eq("")
            & processed_df["phone"].fillna("").astype(str).str.strip().eq("")
        )
        for _, row in processed_df[missing_contact_mask].iterrows():
            severity = "High" if normalize_text(row.get("priority_band")) == "High" else "Medium"
            issues.append(
                build_issue(
                    issue_type="missing_contact_data",
                    severity=severity,
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Chýba web aj telefón.",
                    source_file=row.get("source_file"),
                )
            )

    if not enrichment_df.empty:
        website_leads_mask = enrichment_df["website"].fillna("").astype(str).str.strip().ne("")
        dns_blocked_mask = enrichment_df.apply(is_dns_fetch_blocked, axis=1)
        website_leads_count = int(website_leads_mask.sum())
        dns_blocked_count = int((website_leads_mask & dns_blocked_mask).sum())
        dns_blocked_share = (dns_blocked_count / website_leads_count) if website_leads_count else 0.0

        if website_leads_count and dns_blocked_share >= public_web_fetch_incident_threshold_share:
            issues.append(
                build_issue(
                    issue_type="global_public_web_fetch_incident",
                    severity="High",
                    hotel_name="",
                    city="",
                    priority_band="",
                    details=(
                        "Globálny incident verejného web fetchu: "
                        f"DNS problém zasiahol {dns_blocked_count}/{website_leads_count} leadov s webom "
                        f"(threshold {public_web_fetch_incident_threshold_share:.2f})."
                    ),
                    source_file="",
                )
            )

        missing_summary_mask = enrichment_df["factual_summary"].fillna("").astype(str).str.strip().eq("")
        for _, row in enrichment_df[missing_summary_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="missing_factual_summary",
                    severity="High",
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Chýba factual_summary v enrichment výstupe.",
                    source_file=row.get("source_file"),
                )
            )

        missing_contact_status_mask = enrichment_df["contact_status"].fillna("").astype(str).str.strip().eq("")
        for _, row in enrichment_df[missing_contact_status_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="missing_contact_status",
                    severity="High",
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Chýba contact_status v enrichment výstupe.",
                    source_file=row.get("source_file"),
                )
            )

        unverified_hours_mask = enrichment_df["hotel_opening_hours_status"].fillna("").astype(str).str.strip().eq(
            "Verejne nepotvrdené"
        )
        for _, row in enrichment_df[unverified_hours_mask].iterrows():
            if is_dns_fetch_blocked(row):
                severity = "Low"
                details = "Otváracie hodiny sú verejne nepotvrdené; verejný web fetch bol blokovaný DNS problémom."
            else:
                severity = "Medium" if normalize_text(row.get("priority_band")) == "High" else "Low"
                details = "Otváracie hodiny sú verejne nepotvrdené."
            issues.append(
                build_issue(
                    issue_type="unverified_opening_hours",
                    severity=severity,
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details=details,
                    source_file=row.get("source_file"),
                )
            )

        unverified_checkio_mask = enrichment_df["checkin_checkout_status"].fillna("").astype(str).str.strip().eq(
            "Verejne nepotvrdené"
        ) & enrichment_df["priority_band"].fillna("").astype(str).str.strip().eq("High")
        for _, row in enrichment_df[unverified_checkio_mask].iterrows():
            details = "Check-in / check-out je verejne nepotvrdený pre high-priority lead."
            if is_dns_fetch_blocked(row):
                details = "Check-in / check-out je verejne nepotvrdený; verejný web fetch bol blokovaný DNS problémom."
            issues.append(
                build_issue(
                    issue_type="unverified_checkin_checkout",
                    severity="Low",
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details=details,
                    source_file=row.get("source_file"),
                )
            )

        single_side_verified_mask = enrichment_df.apply(is_single_side_verified_checkin_checkout, axis=1) & (
            enrichment_df["priority_band"].fillna("").astype(str).str.strip().isin(["High", "Medium-High"])
        )
        for _, row in enrichment_df[single_side_verified_mask].iterrows():
            priority_score = pd.to_numeric(row.get("priority_score"), errors="coerce")
            severity = (
                "High"
                if pd.notna(priority_score) and float(priority_score) >= single_side_high_priority_score_threshold
                else "Low"
            )
            issues.append(
                build_issue(
                    issue_type="single_side_verified_checkin_checkout",
                    severity=severity,
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Check-in / check-out je overený len jednostranne; odporúčaný ručný spot-check.",
                    source_file=row.get("source_file"),
                )
            )

    if not clickup_df.empty:
        has_required_columns, missing_required_columns = has_clickup_required_columns(clickup_df)
        if not has_required_columns:
            issues.append(
                build_issue(
                    issue_type="missing_clickup_required_columns",
                    severity="High",
                    hotel_name="",
                    city="",
                    priority_band="",
                    details="Chýbajú povinné ClickUp stĺpce: " + ", ".join(missing_required_columns),
                    source_file="",
                )
            )
            return pd.DataFrame(issues)

        missing_core_columns = [
            column for column in CLICKUP_SUPPORTED_CORE_COLUMNS if column not in clickup_df.columns
        ]
        if missing_core_columns:
            issues.append(
                build_issue(
                    issue_type="missing_clickup_core_columns",
                    severity="High",
                    hotel_name="",
                    city="",
                    priority_band="",
                    details="Chýbajú odporúčané ClickUp core stĺpce: " + ", ".join(missing_core_columns),
                    source_file="",
                )
            )

        if len(clickup_df) > 10000:
            issues.append(
                build_issue(
                    issue_type="clickup_row_limit_exceeded",
                    severity="High",
                    hotel_name="",
                    city="",
                    priority_band="",
                    details="ClickUp spreadsheet import limit 10 000 riadkov je prekročený.",
                    source_file="",
                )
            )

        duplicate_task_mask = clickup_df.duplicated(subset=["Task name"], keep=False)
        for _, row in clickup_df[duplicate_task_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="duplicate_clickup_task",
                    severity="High",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Duplicitný ClickUp Task name.",
                    source_file=row.get("Source file"),
                )
            )

        empty_task_name_mask = clickup_df["Task name"].fillna("").astype(str).str.strip().eq("")
        for _, row in clickup_df[empty_task_name_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="missing_clickup_task_name",
                    severity="High",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Chýba Task name pre ClickUp export.",
                    source_file=row.get("Source file"),
                )
            )

        empty_description_mask = clickup_df["Description content"].fillna("").astype(str).str.strip().eq("")
        for _, row in clickup_df[empty_description_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="missing_clickup_description",
                    severity="Low",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Chýba Description content pre ClickUp export.",
                    source_file=row.get("Source file"),
                )
            )

        invalid_status_mask = ~clickup_df["Status"].fillna("").astype(str).str.strip().str.lower().isin(
            ["to do", "todo", "open", "backlog", "in progress", "complete", "done"]
        )
        for _, row in clickup_df[invalid_status_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="invalid_clickup_status",
                    severity="Medium",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Status nie je v bezpečnom importnom sete.",
                    source_file=row.get("Source file"),
                )
            )

        normalized_priorities = clickup_df["Priority"].apply(normalize_clickup_priority_value)
        invalid_priority_mask = ~normalized_priorities.isin(["", "1", "2", "3", "4"])
        for _, row in clickup_df[invalid_priority_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="invalid_clickup_priority",
                    severity="Medium",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Priority nie je v očakávanom ClickUp numeric sete 1-4.",
                    source_file=row.get("Source file"),
                )
            )

        empty_status_mask = clickup_df["Status"].fillna("").astype(str).str.strip().eq("")
        for _, row in clickup_df[empty_status_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="missing_clickup_status",
                    severity="Low",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Status chýba; pri importe bude treba ručné mapovanie alebo default.",
                    source_file=row.get("Source file"),
                )
            )

    if not issues:
        return pd.DataFrame(
            [
                build_issue(
                    issue_type="no_issues_found",
                    severity="OK",
                    hotel_name="",
                    city="",
                    priority_band="",
                    details="QA nenašlo žiadne problémy podľa aktuálnych pravidiel.",
                    source_file="",
                )
            ]
        )

    return pd.DataFrame(issues)


def save_qa_outputs(issues_df: pd.DataFrame) -> tuple[Path, Path]:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    issues_path = QA_DIR / "qa_issues.csv"
    summary_path = QA_DIR / "qa_summary.txt"

    issues_df.to_csv(issues_path, index=False)

    blocking_count = len(issues_df[issues_df["blocking"] == "yes"])
    high_count = len(issues_df[issues_df["severity"] == "High"])
    medium_count = len(issues_df[issues_df["severity"] == "Medium"])
    low_count = len(issues_df[issues_df["severity"] == "Low"])
    ok_count = len(issues_df[issues_df["severity"] == "OK"])

    summary_lines = [
        f"Počet QA issue riadkov: {len(issues_df)}",
        f"Blocking: {blocking_count}",
        f"High: {high_count}",
        f"Medium: {medium_count}",
        f"Low: {low_count}",
        f"OK: {ok_count}",
    ]
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    return issues_path, summary_path


def save_manual_review_shortlist(
    enrichment_df: pd.DataFrame,
    qa_df: pd.DataFrame,
) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    shortlist_path = MANUAL_REVIEW_SHORTLIST_PATH
    qa_config = load_qa_config().get("qa", {})
    high_lead_clickup_ready_score_threshold = float(
        qa_config.get("high_lead_clickup_ready_score_threshold", 9.0)
    )

    if enrichment_df.empty:
        pd.DataFrame(
            columns=[
                "hotel_name",
                "city",
                "priority_band",
                "priority_score",
                "review_bucket",
                "operator_triage_priority",
                "operator_triage_action",
                "hotel_opening_hours_status",
                "checkin_checkout_status",
                "checkin_checkout_source_origin",
                "checkin_checkout_completeness",
                "public_source_reachable",
                "public_source_fetch_status",
                "manual_review_reason",
                "source_file",
            ]
        ).to_csv(shortlist_path, index=False)
        return shortlist_path

    shortlist_df = enrichment_df.copy()
    shortlist_df["manual_review_reason"] = ""

    needs_review_mask = (
        shortlist_df["priority_band"].fillna("").astype(str).str.strip().isin(["High", "Medium-High"])
        & (
            shortlist_df["hotel_opening_hours_status"].fillna("").astype(str).str.strip().eq("Verejne nepotvrdené")
            | shortlist_df["checkin_checkout_status"].fillna("").astype(str).str.strip().eq("Verejne nepotvrdené")
            | shortlist_df["checkin_checkout_completeness"].fillna("").astype(str).str.strip().eq("single_side")
        )
    )

    shortlist_df = shortlist_df[needs_review_mask].copy()
    if shortlist_df.empty:
        shortlist_df = pd.DataFrame(
            columns=[
                "hotel_name",
                "city",
                "priority_band",
                "priority_score",
                "review_bucket",
                "operator_triage_priority",
                "operator_triage_action",
                "hotel_opening_hours_status",
                "checkin_checkout_status",
                "checkin_checkout_source_origin",
                "checkin_checkout_completeness",
                "public_source_reachable",
                "public_source_fetch_status",
                "manual_review_reason",
                "source_file",
            ]
        )
        shortlist_df.to_csv(shortlist_path, index=False)
        return shortlist_path

    def build_reason(row: pd.Series) -> str:
        reasons: list[str] = []
        reachable = normalize_text(row.get("public_source_reachable")) == "yes"
        dns_blocked = is_dns_fetch_blocked(row)
        if normalize_text(row.get("hotel_opening_hours_status")) == "Verejne nepotvrdené":
            reasons.append(
                "reachable_but_missing_opening_hours" if reachable else "unverified_opening_hours"
            )
        if normalize_text(row.get("checkin_checkout_status")) == "Verejne nepotvrdené":
            reasons.append(
                "reachable_but_missing_checkin_checkout" if reachable else "unverified_checkin_checkout"
            )
        if is_single_side_verified_checkin_checkout(row):
            reasons.append("single_side_verified_checkin_checkout")
        if normalize_text(row.get("public_source_reachable")) != "yes":
            reasons.append("source_fetch_blocked_dns" if dns_blocked else "source_not_reachable")
        return " | ".join(reasons)

    def build_review_bucket(row: pd.Series) -> str:
        reachable = normalize_text(row.get("public_source_reachable")) == "yes"
        missing_opening = normalize_text(row.get("hotel_opening_hours_status")) == "Verejne nepotvrdené"
        missing_checkio = normalize_text(row.get("checkin_checkout_status")) == "Verejne nepotvrdené"
        dns_blocked = is_dns_fetch_blocked(row)

        if reachable and missing_checkio:
            return "reachable_missing_checkin_checkout"
        if is_single_side_verified_checkin_checkout(row):
            return "single_side_verified_needs_review"
        if reachable and missing_opening:
            return "reachable_missing_opening_hours"
        if dns_blocked:
            return "dns_fetch_blocked"
        return "source_unreachable_or_lower_signal"

    def build_operator_triage_priority(row: pd.Series) -> str:
        priority_band = normalize_text(row.get("priority_band"))
        if priority_band == "High":
            return "P1"
        if priority_band == "Medium-High":
            return "P2"
        return "P3"

    def build_operator_triage_action(row: pd.Series) -> str:
        priority_band = normalize_text(row.get("priority_band"))
        review_bucket = normalize_text(row.get("review_bucket"))
        priority_score = pd.to_numeric(row.get("priority_score"), errors="coerce")
        top_high_lead = (
            priority_band == "High"
            and pd.notna(priority_score)
            and float(priority_score) >= high_lead_clickup_ready_score_threshold
        )

        if review_bucket == "dns_fetch_blocked":
            return "hold_batch_due_to_dns_incident" if priority_band == "High" else "hold_for_retry"
        if review_bucket == "single_side_verified_needs_review":
            return "manual_spotcheck_then_clickup" if top_high_lead else "manual_spotcheck"
        if review_bucket in {"reachable_missing_checkin_checkout", "reachable_missing_opening_hours"}:
            return "manual_review_before_clickup" if priority_band == "High" else "manual_review_if_capacity"
        return "review_before_clickup" if priority_band == "High" else "defer_review"

    shortlist_df["manual_review_reason"] = shortlist_df.apply(build_reason, axis=1)
    shortlist_df["review_bucket"] = shortlist_df.apply(build_review_bucket, axis=1)
    shortlist_df["operator_triage_priority"] = shortlist_df.apply(build_operator_triage_priority, axis=1)
    shortlist_df["operator_triage_action"] = shortlist_df.apply(build_operator_triage_action, axis=1)
    shortlist_df["_reachable_rank"] = shortlist_df["public_source_reachable"].fillna("").astype(str).str.strip().eq("yes").map(
        {True: 0, False: 1}
    )
    shortlist_df["_priority_rank"] = shortlist_df["priority_band"].fillna("").astype(str).str.strip().map(
        {"High": 0, "Medium-High": 1}
    ).fillna(2)
    shortlist_df["_checkio_rank"] = shortlist_df["checkin_checkout_status"].fillna("").astype(str).str.strip().eq(
        "Verejne nepotvrdené"
    ).map({True: 0, False: 1})
    shortlist_df["_single_side_rank"] = shortlist_df["checkin_checkout_completeness"].fillna("").astype(str).str.strip().eq(
        "single_side"
    ).map({True: 0, False: 1})
    shortlist_df = shortlist_df.sort_values(
        by=["_reachable_rank", "_priority_rank", "_checkio_rank", "_single_side_rank", "priority_score"],
        ascending=[True, True, True, True, False],
        kind="stable",
    )
    shortlist_df = shortlist_df[
        [
            "hotel_name",
            "city",
            "priority_band",
            "priority_score",
            "review_bucket",
            "operator_triage_priority",
            "operator_triage_action",
            "hotel_opening_hours_status",
            "checkin_checkout_status",
            "checkin_checkout_source_origin",
            "checkin_checkout_completeness",
            "public_source_reachable",
            "public_source_fetch_status",
            "manual_review_reason",
            "source_file",
        ]
    ].copy()
    shortlist_df.to_csv(shortlist_path, index=False)
    return shortlist_path


def main() -> None:
    processed_df = load_csv(get_first_file(PROCESSED_DIR, "*_normalized_scored.csv"))
    enrichment_df = load_csv(get_first_file(ENRICHMENT_DIR, "*_enriched.csv"))
    clickup_df = load_csv(get_first_file(CLICKUP_DIR, "*_clickup_import.csv"))

    issues_df = build_issue_rows(
        processed_df=processed_df,
        enrichment_df=enrichment_df,
        clickup_df=clickup_df,
    )
    issues_path, summary_path = save_qa_outputs(issues_df)
    shortlist_path = save_manual_review_shortlist(enrichment_df, issues_df)

    print(f"QA issues uložené do: {issues_path}")
    print(f"QA summary uložené do: {summary_path}")
    print(f"Manual review shortlist uložený do: {shortlist_path}")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(issues_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
