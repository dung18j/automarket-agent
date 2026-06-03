#!/usr/bin/env python3
import os
import re
import sys
import time
import subprocess
from pathlib import Path

AGENT_REPO = Path(__file__).parent.resolve()
PROJECT_REPO = "git@github.com:dung18j/automarket.git"
PROJECT_DIR = Path("/tmp/opencode/automarket")
TICKET_DIR = AGENT_REPO / "ticket"
POLL_INTERVAL = 15


def log(msg):
    print(f"[agent] {msg}", flush=True)


def get_tickets(stage):
    result = []
    for f in sorted(TICKET_DIR.glob("*.md")):
        m = re.search(r"^stage:\s*(\S+)", f.read_text(), re.MULTILINE)
        if m and m.group(1) == stage:
            result.append(f)
    return result


def set_stage(path, stage):
    text = path.read_text()
    text = re.sub(r"^stage:\s*\S+", f"stage: {stage}", text, flags=re.MULTILINE)
    path.write_text(text)


def read_description(path):
    text = path.read_text()
    m = re.match(r"^---\n.*?\n---\n(.+)", text, re.DOTALL)
    return m.group(1).strip() if m else text.strip()


def git_commit_push(repo, msg, branch=None):
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True, text=True)
    r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo, capture_output=True)
    if r.returncode != 0:
        subprocess.run(["git", "commit", "-m", msg], cwd=repo, capture_output=True, text=True)
    if branch:
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=repo, capture_output=True, text=True)
    else:
        subprocess.run(["git", "push"], cwd=repo, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True, text=True)


def claim_ticket(ticket_path):
    log(f"Claim {ticket_path.name} -> doing")
    set_stage(ticket_path, "doing")
    git_commit_push(AGENT_REPO, f"Claim {ticket_path.stem}: move to doing")


def finish_ticket(ticket_path):
    log(f"Finish {ticket_path.name} -> need_review")
    set_stage(ticket_path, "need_review")
    git_commit_push(AGENT_REPO, f"{ticket_path.stem}: move to need_review")


def ensure_project():
    if not PROJECT_DIR.exists():
        log(f"Clone {PROJECT_REPO}")
        subprocess.run(["git", "clone", PROJECT_REPO, str(PROJECT_DIR)], capture_output=True, text=True)
    subprocess.run(["git", "pull", "--rebase"], cwd=PROJECT_DIR, capture_output=True, text=True)


def create_ticket_branch(ticket_stem):
    branch = f"ticket/{ticket_stem}"
    log(f"Switching to branch {branch}")
    subprocess.run(["git", "checkout", "main"], cwd=PROJECT_DIR, capture_output=True, text=True)
    subprocess.run(["git", "branch", "-D", branch], cwd=PROJECT_DIR, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", branch], cwd=PROJECT_DIR, capture_output=True, text=True)
    return branch


def run_opencode(ticket_path, description):
    msg = (
        f"Implement this ticket: {ticket_path.stem}\n\n"
        f"Description:\n{description}\n\n"
        f"Make the necessary changes to the project."
    )
    log(f"Running opencode for {ticket_path.name}...")
    r = subprocess.run(
        ["opencode", "run", "--dir", str(PROJECT_DIR),
         "--dangerously-skip-permissions", msg],
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        log(f"opencode failed: {r.stderr.strip()[-300:]}")
        return "", False
    log(f"opencode done")
    output = (r.stdout or "") + "\n" + (r.stderr or "")
    return output.strip(), True


def add_ticket_comment(ticket_path, comment):
    text = ticket_path.read_text()
    convo_marker = "## Conversation"
    if convo_marker in text:
        text = text.replace(
            convo_marker,
            f"{convo_marker}\n\n"
            f"_opencode comment @ {time.strftime('%Y-%m-%d %H:%M:%S')}_\n\n{comment}",
        )
    else:
        text += (f"\n\n{convo_marker}\n\n"
                 f"_opencode comment @ {time.strftime('%Y-%m-%d %H:%M:%S')}_\n\n{comment}")
    ticket_path.write_text(text)


def main():
    log(f"Agent started – polling every {POLL_INTERVAL}s")
    while True:
        for stage in ("need_fix", "todo"):
            tickets = get_tickets(stage)
            if not tickets:
                continue
            ticket_path = tickets[0]
            description = read_description(ticket_path)

            claim_ticket(ticket_path)
            ensure_project()
            branch = create_ticket_branch(ticket_path.stem)
            output, ok = run_opencode(ticket_path, description)

            if ok:
                add_ticket_comment(ticket_path, output)
                git_commit_push(PROJECT_DIR, f"Implement {ticket_path.stem}", branch)
                finish_ticket(ticket_path)
            else:
                log(f"Reverting {ticket_path.name} to {stage}")
                set_stage(ticket_path, stage)
                git_commit_push(AGENT_REPO, f"{ticket_path.stem}: revert to {stage}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
