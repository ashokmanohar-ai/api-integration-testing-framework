"""Start and validate the complete Docker Compose test environment."""

import subprocess
import sys


def main() -> None:
    subprocess.run(["docker", "compose", "up", "-d", "--build"], check=True)
    subprocess.run([sys.executable, "scripts/wait_for_services.py"], check=True)


if __name__ == "__main__":
    main()
