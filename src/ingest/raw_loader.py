from pathlib import Path
import pandas as pd


RAW_DIR = Path("data/raw")


def list_raw_csv_files(raw_dir: Path = RAW_DIR) -> list[Path]:
    if not raw_dir.exists():
        return []
    return sorted(raw_dir.glob("*.csv"), key=lambda path: path.stat().st_mtime)


def load_raw_csv(file_path: Path) -> pd.DataFrame:
    return pd.read_csv(file_path)


def build_raw_preview(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    preview = df.copy()
    preview["source_file"] = source_file
    return preview


def main() -> None:
    csv_files = list_raw_csv_files()

    if not csv_files:
        print("V priečinku data/raw nie je žiadny CSV súbor.")
        return

    first_file = csv_files[0]
    try:
        df = load_raw_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    preview = build_raw_preview(df, first_file.name)

    print(f"Načítaný súbor: {first_file.name}")
    print(f"Počet riadkov: {len(preview)}")
    print(f"Počet stĺpcov: {len(preview.columns)}")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(preview.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
