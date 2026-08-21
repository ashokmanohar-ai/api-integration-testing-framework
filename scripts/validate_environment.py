"""Validate selected settings before running a suite."""

from config.settings import ConfigurationError, load_settings


def main() -> None:
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        raise SystemExit(f"CONFIGURATION ERROR: {exc}") from exc
    print(
        f"Environment '{settings.environment}' is valid; "
        f"API target is {settings.api_base_url}. Secrets were not displayed."
    )


if __name__ == "__main__":
    main()
