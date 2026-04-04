import argparse

from orchestrate import main as run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hotel Lead Enrichment Engine OS")
    parser.add_argument(
        "--skip-orchestration",
        action="store_true",
        help="Spustí pipeline bez orchestration dry run kroku.",
    )
    parser.add_argument(
        "--orchestration-only",
        action="store_true",
        help="Spustí iba orchestration runner.",
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
