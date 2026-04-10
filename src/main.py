import argparse

from orchestrate import main as run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Hotel Lead Enrichment Engine OS: canonical pipeline "
            "normalize -> factual/source_bundle -> commercial_synthesizer(v3-lite) "
            "-> ranking_refresh -> email_drafts -> master_exports "
            "-> render_full_enrichment_md -> clickup_export -> QA/gate -> Make"
        )
    )
    parser.add_argument(
        "--skip-orchestration",
        action="store_true",
        help="Spustí kanonický Python pipeline bez Make orchestration kroku.",
    )
    parser.add_argument(
        "--orchestration-only",
        action="store_true",
        help="Spustí iba Make orchestration runner nad existujúcimi artifactmi.",
    )
    parser.add_argument(
        "--orchestration-mode",
        choices=["dry_run", "validate_only"],
        default="dry_run",
        help="Režim orchestration kroku.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.orchestration_only:
        from make_orchestration_runner import run as run_make_orchestration

        result = run_make_orchestration(
            mode=args.orchestration_mode,
            scenario_label="main_orchestration_only",
        )
        print(result)
    else:
        run_pipeline(
            include_orchestration=not args.skip_orchestration,
            orchestration_mode=args.orchestration_mode,
        )
