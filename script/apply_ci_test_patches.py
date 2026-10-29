"""Apply explicit fixture repairs to installed upstream release tests only.

Run after pip installation in assembly CI. A changed upstream fixture fails
the dry run so the patch must be reviewed or removed instead of silently skipped.
"""
from pathlib import Path
import subprocess
import sysconfig


def main():
    site_packages = sysconfig.get_path("purelib")
    patches = sorted(Path(__file__).with_name("ci-test-patches").glob("*.patch"))
    for patch in patches:
        command = ["patch", "--batch", "--forward", "--fuzz=0", "-p0", "-i", str(patch.resolve())]
        subprocess.run([*command, "--dry-run"], cwd=site_packages, check=True)
        subprocess.run(command, cwd=site_packages, check=True)


if __name__ == "__main__":
    main()
