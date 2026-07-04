#!/usr/bin/env python3
"""Render remote Git development workflow command snippets from a JSON config."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED = [
    "project_name",
    "local_dir",
    "remote_host_alias",
    "remote_project_dir",
    "center_remote_url",
]


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def sh_path_quote(value: str) -> str:
    if value == "~":
        return "~"
    if value.startswith("~/"):
        rest = value[2:]
        if re.fullmatch(r"[A-Za-z0-9_./@%+=:,~-]+", rest):
            return "~/" + rest
        return "~/" + sh_quote(rest)
    return sh_quote(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path, help="JSON file with workflow values")
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    missing = [key for key in REQUIRED if not config.get(key)]
    if missing:
        raise SystemExit(f"Missing required config keys: {', '.join(missing)}")

    branch = config.get("default_branch", "main")
    local_dir = config["local_dir"]
    remote = config["remote_host_alias"]
    remote_dir = config["remote_project_dir"]
    remote_deploy_dir = config.get("remote_deploy_dir", f"~/Deploy/{config['project_name']}")
    center = config["center_remote_url"]
    mode = config.get("mode", "ssh-sync")

    if mode not in {"ssh-sync", "server-pull"}:
        raise SystemExit("mode must be 'ssh-sync' or 'server-pull'")

    print("# Local remotes")
    print(f"git -C {ps_quote(local_dir)} remote add origin {center}")
    print(f"git -C {ps_quote(local_dir)} branch -M {branch}")
    print()

    print("# Push to center remote")
    print(f"git -C {ps_quote(local_dir)} push -u origin {branch}")
    print()

    if mode == "ssh-sync":
        print("# SSH snapshot deploy")
        print(f"$status = git -C {ps_quote(local_dir)} status --short")
        print('if ($status) { Write-Error "Refusing to deploy: commit or discard local changes first."; exit 2 }')
        print(f"$commit = (git -C {ps_quote(local_dir)} rev-parse --short=12 HEAD).Trim()")
        print(f"$release = {ps_quote(remote_deploy_dir + '/releases/')} + $commit")
        print(f'ssh {remote} "mkdir -p \'$release\'"')
        print(
            f"git -C {ps_quote(local_dir)} archive --format=tar HEAD | "
            f"ssh {remote} \"tar -xf - -C '$release' && printf '%s\\n' '$commit' > '$release/.deploy_commit' && ln -sfn '$release' {sh_path_quote(remote_deploy_dir + '/current')}\""
        )
        print()
        print("# Remote smoke test")
        smoke_cmd = f"cd {sh_path_quote(remote_deploy_dir + '/current')} && bash eval/run_smoke_test.sh"
        print(f"ssh {remote} {ps_quote(smoke_cmd)}")
    else:
        print("# Configure server origin")
        remote_cmd = (
            f"cd {sh_path_quote(remote_dir)} && "
            f"git remote set-url origin {sh_quote(center)} || "
            f"git remote add origin {sh_quote(center)}"
        )
        print(f"ssh {remote} {ps_quote(remote_cmd)}")
        print()

        print("# Remote update")
        update_cmd = f"cd {sh_path_quote(remote_dir)} && bash scripts/remote_update.sh"
        print(f"ssh {remote} {ps_quote(update_cmd)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
