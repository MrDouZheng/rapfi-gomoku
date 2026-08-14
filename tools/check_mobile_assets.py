# SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
# SPDX-License-Identifier: GPL-3.0-only

"""Fail when the Android and iOS copies of shared mobile assets drift."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android" / "app" / "src" / "main" / "assets"
IOS = ROOT / "ios" / "DouYi" / "Web"
SHARED = ("index.html", "app.js", "engine-worker.js", "styles.css")


def main() -> None:
    mismatches = [name for name in SHARED if (ANDROID / name).read_bytes() != (IOS / name).read_bytes()]
    if mismatches:
        raise SystemExit(f"mobile assets differ: {', '.join(mismatches)}")
    print(f"mobile assets match: {', '.join(SHARED)}")


if __name__ == "__main__":
    main()
