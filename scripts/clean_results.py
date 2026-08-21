"""Remove generated reports without touching source or test evidence elsewhere."""

from pathlib import Path


def main() -> None:
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    for path in reports.iterdir():
        if path.name != ".gitkeep" and path.is_file():
            path.unlink()
    print("Generated report files removed")


if __name__ == "__main__":
    main()
