#!/usr/bin/env python3
"""Collect read-only Dependabot alert and pull-request context as JSON."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any


class CollectionError(RuntimeError):
    """Raised when required GitHub context cannot be collected safely."""


def run_gh(arguments: list[str]) -> str:
    result = subprocess.run(
        ["gh", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown gh error"
        raise CollectionError(detail)
    return result.stdout


def run_gh_json(arguments: list[str]) -> Any:
    output = run_gh(arguments)
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise CollectionError(f"gh returned invalid JSON: {error}") from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Dependabot alerts and Dependabot-authored PRs without mutating GitHub."
    )
    parser.add_argument(
        "--repo",
        help="Repository in OWNER/REPO form. Defaults to the repository for the current checkout.",
    )
    parser.add_argument(
        "--alert-state",
        choices=("open", "dismissed", "fixed", "auto_dismissed"),
        default="open",
        help="Dependabot alert state to collect (default: open).",
    )
    parser.add_argument(
        "--pr-state",
        choices=("open", "closed", "merged", "all"),
        default="open",
        help="Dependabot PR state to collect (default: open).",
    )
    parser.add_argument(
        "--pr-limit",
        type=int,
        default=200,
        help="Maximum Dependabot PRs to collect (default: 200).",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of indented JSON.",
    )
    return parser.parse_args()


def validate_repo(repo: str) -> str:
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repo):
        raise CollectionError("repository must use OWNER/REPO form")
    return repo


def flatten_pages(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise CollectionError("unexpected paginated alert response")

    flattened: list[dict[str, Any]] = []
    for page in value:
        if not isinstance(page, list):
            raise CollectionError("unexpected alert page shape")
        for item in page:
            if not isinstance(item, dict):
                raise CollectionError("unexpected alert item shape")
            flattened.append(item)
    return flattened


def main() -> int:
    args = parse_args()
    if args.pr_limit < 1:
        raise CollectionError("--pr-limit must be positive")
    if shutil.which("gh") is None:
        raise CollectionError("GitHub CLI (gh) is required")

    run_gh(["auth", "status"])

    if args.repo:
        repo_name = validate_repo(args.repo)
    else:
        discovered = run_gh_json(["repo", "view", "--json", "nameWithOwner"])
        repo_name = validate_repo(discovered["nameWithOwner"])

    repository = run_gh_json(
        [
            "repo",
            "view",
            repo_name,
            "--json",
            "nameWithOwner,url,defaultBranchRef,isPrivate,viewerPermission",
        ]
    )

    alert_pages = run_gh_json(
        [
            "api",
            "--method",
            "GET",
            "--paginate",
            "--slurp",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
            "-f",
            f"state={args.alert_state}",
            "-F",
            "per_page=100",
            f"repos/{repo_name}/dependabot/alerts",
        ]
    )
    alerts = flatten_pages(alert_pages)

    prs = run_gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo_name,
            "--state",
            args.pr_state,
            "--app",
            "dependabot",
            "--limit",
            str(args.pr_limit),
            "--json",
            (
                "number,title,url,author,headRefName,baseRefName,isDraft,labels,"
                "mergeable,mergeStateStatus,statusCheckRollup,createdAt,updatedAt"
            ),
        ]
    )
    if not isinstance(prs, list):
        raise CollectionError("unexpected pull-request response")

    result = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "repository": repository,
        "filters": {
            "alert_state": args.alert_state,
            "pr_state": args.pr_state,
            "pr_limit": args.pr_limit,
        },
        "dependabot_alerts": alerts,
        "dependabot_pull_requests": prs,
    }
    json.dump(
        result,
        sys.stdout,
        indent=None if args.compact else 2,
        separators=(",", ":") if args.compact else None,
        sort_keys=True,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CollectionError as error:
        print(f"collect-context: {error}", file=sys.stderr)
        raise SystemExit(1) from error
