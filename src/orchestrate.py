from normalize_score import main as run_normalize_score
from functools import partial

from enrich_hotels import main as run_enrich
from commercial_synthesizer import main as run_commercial_synthesizer
from ranking_refresh import main as run_ranking_refresh
from email_drafts import main as run_email_drafts
from master_exports import main as run_master_exports
from render_full_enrichment_md import main as run_render_full_enrichment_md
from clickup_export import main as run_clickup_export
from qa_checks import main as run_qa_checks
from run_report import main as run_report
from run_manifest import main as run_manifest
from clickup_import_gate import main as run_clickup_import_gate
from clickup_dry_run_sample import main as run_clickup_dry_run_sample
from clickup_api_mapping_preview import main as run_clickup_api_mapping_preview
from high_leads_preimport_checklist import main as run_high_leads_preimport_checklist
from operator_decision_summary import main as run_operator_decision_summary
from archive_run_artifacts import main as run_archive_run_artifacts
from archive_cleanup import main as run_archive_cleanup
from make_orchestration_runner import run as run_make_orchestration


def build_pipeline_steps(
    include_orchestration: bool = True,
    orchestration_mode: str = "dry_run",
) -> list[tuple[str, object]]:
    steps = [
        ("normalize", run_normalize_score),
        ("factual/source_bundle", run_enrich),
        ("commercial_synthesizer (v3-lite)", run_commercial_synthesizer),
        ("ranking refresh", run_ranking_refresh),
        ("email drafts", run_email_drafts),
        ("master exports", run_master_exports),
        ("render full enrichment markdown", run_render_full_enrichment_md),
        ("ClickUp export", run_clickup_export),
        ("QA", run_qa_checks),
        ("run summary", run_report),
        ("run manifest", run_manifest),
        ("ClickUp import gate", run_clickup_import_gate),
        ("ClickUp dry run sample", run_clickup_dry_run_sample),
        ("ClickUp API mapping preview", run_clickup_api_mapping_preview),
        ("High leads pre-import checklist", run_high_leads_preimport_checklist),
        ("Operator decision summary", run_operator_decision_summary),
        ("run manifest final", run_manifest),
        ("archive run artifacts", run_archive_run_artifacts),
        ("archive cleanup", run_archive_cleanup),
    ]
    if include_orchestration:
        steps.append(
            (
                "Make orchestration dry run",
                partial(run_make_orchestration, mode=orchestration_mode, scenario_label="pipeline_default"),
            )
        )
    return steps


def main(
    include_orchestration: bool = True,
    orchestration_mode: str = "dry_run",
) -> None:
    print("Spúšťam kanonický pipeline Hotel Lead Enrichment Engine OS.")

    for step_name, step_function in build_pipeline_steps(
        include_orchestration=include_orchestration,
        orchestration_mode=orchestration_mode,
    ):
        print(f"\n--- {step_name} ---")
        step_function()

    print("\nPipeline dokončený.")


if __name__ == "__main__":
    main()
