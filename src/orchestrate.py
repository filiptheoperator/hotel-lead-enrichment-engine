from normalize_score import main as run_normalize_score
from enrich_hotels import main as run_enrich
from email_drafts import main as run_email_drafts
from clickup_export import main as run_clickup_export
from qa_checks import main as run_qa_checks
from run_report import main as run_report


PIPELINE_STEPS = [
    ("normalize + score", run_normalize_score),
    ("enrich", run_enrich),
    ("email drafts", run_email_drafts),
    ("ClickUp export", run_clickup_export),
    ("QA", run_qa_checks),
    ("run summary", run_report),
]


def main() -> None:
    print("Spúšťam pipeline Hotel Lead Enrichment Engine OS.")

    for step_name, step_function in PIPELINE_STEPS:
        print(f"\n--- {step_name} ---")
        step_function()

    print("\nPipeline dokončený.")


if __name__ == "__main__":
    main()
