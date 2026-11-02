"""Verify every pinned Python dependency before installation, using PyPI metadata."""

import argparse
import concurrent.futures
import json
import re
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    npm_config = (ROOT / "frontend/.npmrc").read_text()
    frozen = re.search(r"^before=(.+)$", npm_config, re.MULTILINE).group(1)
    cutoff = min(
        datetime.fromisoformat(frozen.replace("Z", "+00:00")), datetime.now(UTC) - timedelta(days=4)
    )
    packages = {}
    for filename in ("requirements-ci.txt", "requirements-tooling.txt"):
        for line in (ROOT / filename).read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9.+!_-]+)", line)
            if not match:
                raise ValueError(f"Unpinned requirement in {filename}")
            packages[match.group(1)] = match.group(2)

    def check(item):
        name, version = item
        with urllib.request.urlopen(
            f"https://pypi.org/pypi/{name}/{version}/json", timeout=30
        ) as response:
            metadata = json.load(response)
        files = metadata["urls"]
        if not files or any(file.get("yanked") for file in files):
            raise ValueError(f"{name}=={version}: missing or yanked release")
        published = max(
            datetime.fromisoformat(file["upload_time_iso_8601"].replace("Z", "+00:00"))
            for file in files
        )
        if published > cutoff:
            raise ValueError(f"{name}=={version}: published {published.isoformat()}, after cutoff")
        return {
            "name": name,
            "version": version,
            "latestArtifactPublishedAt": published.isoformat(),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        records = list(executor.map(check, sorted(packages.items())))
    if args.write:
        target = ROOT / "validation/python-dependencies-release-audit.json"
        target.write_text(
            json.dumps({"cutoff": cutoff.isoformat(), "packages": records}, indent=2) + "\n"
        )
    print(
        f"Verified all {len(records)} pinned Python versions were published by {cutoff.isoformat()}."
    )


if __name__ == "__main__":
    main()
