#!/usr/bin/env python3
import json
import os
import re
import sys
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AGENT_REPO = Path(__file__).parent.resolve()
PROJECT_REPO = "git@github.com:dung18j/automarket.git"
PROJECT_DIR = Path("/tmp/opencode/automarket")
TICKET_DIR = AGENT_REPO / "ticket"
POLL_INTERVAL = 15


def log(msg):
    print(f"[agent] {msg}", flush=True)


TRANSITIONS_LOG = AGENT_REPO / "transitions.jsonl"


def log_transition(ticket, role, from_stage, to_stage, status, details=""):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket": ticket.name,
        "role": role,
        "from": from_stage,
        "to": to_stage,
        "status": status,
        "details": details,
    }
    with open(TRANSITIONS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    log(f"[transition] {role}: {ticket.name} {from_stage} -> {to_stage} ({status})")


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


def get_stage(path):
    m = re.search(r"^stage:\s*(\S+)", path.read_text(), re.MULTILINE)
    return m.group(1) if m else None


def get_depend_on(path):
    text = path.read_text()
    m = re.search(r"^depend_on:\s*\[([^\]]*)\]", text, re.MULTILINE)
    if m:
        raw = m.group(1).strip()
        return [s.strip() for s in raw.split(",") if s.strip()]
    m = re.search(r"^depend_on:\s*(\S+)", text, re.MULTILINE)
    return [m.group(1).strip()] if m else []


def set_depend_on(path, deps):
    text = path.read_text()
    dep_str = f"[{', '.join(deps)}]"
    if re.search(r"^depend_on:", text, re.MULTILINE):
        text = re.sub(r"^depend_on:.*", f"depend_on: {dep_str}", text, flags=re.MULTILINE)
    else:
        text = re.sub(r"^(stage:.*)", rf"\1\ndepend_on: {dep_str}", text, flags=re.MULTILINE)
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


def dependencies_satisfied(path):
    deps = get_depend_on(path)
    if not deps:
        return True
    for stem in deps:
        dep_path = TICKET_DIR / f"{stem}.md"
        if not dep_path.exists():
            return False
        if get_stage(dep_path) != "done":
            return False
    return True


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

def run_opencode_admin(ticket_path, description):
    msg = (
        f"You are acting as a admin. Refine the draft ticket: {ticket_path.stem}\n\n"
        f"Current Description:\n{description}\n\n"
        f"1. Read the project source code in {PROJECT_DIR} to understand the context.\n"
        f"2. If the task is complex, break it down into sub-tasks. For each sub-task, create a new ticket file in {TICKET_DIR} "
        f"with a descriptive filename like '{ticket_path.stem}-subtask-name.md'. Each sub-ticket must have front-matter with "
        f"'stage: todo'. Update the parent ticket's `depend_on` field to list all created sub-tickets.\n"
        f"3. Update the parent ticket file at {ticket_path} with detailed technical information and a clear step-by-step instruction for the developer.\n"
        f"Ensure the ticket remains in the same format (front-matter and description)."
    )
    log(f"Admin refining {ticket_path.name}...")
    r = subprocess.run(
        ["opencode", "run", "--dir", str(PROJECT_DIR), "--dangerously-skip-permissions", msg],
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        log(f"opencode failed: {r.stderr.strip()[-300:]}")
        return "", False
    log(f"opencode done")
    return ((r.stdout or "") + "\n" + (r.stderr or "")).strip(), True


def run_opencode_manager(ticket_path, description):
    msg = (
        f"You are acting as a manager. Review the refined ticket: {ticket_path.stem}\n\n"
        f"Description:\n{description}\n\n"
        f"Read the project source code in {PROJECT_DIR} to verify technical feasibility.\n"
        f"Update ticket stage to `todo` if the ticket has enough detail and clear instructions to be implemented.\n"
        f"Update its `stage` to 'draft' if the ticket needs more information or corrections, add a 'Comment:' section at the end of the file "
        f"explaining what's missing, then ."
    )
    log(f"Manager reviewing {ticket_path.name}...")
    r = subprocess.run(
        ["opencode", "run", "--dir", str(PROJECT_DIR), "--dangerously-skip-permissions", msg],
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        log(f"opencode failed: {r.stderr.strip()[-300:]}")
        return "", False
    log(f"opencode done")
    return ((r.stdout or "") + "\n" + (r.stderr or "")).strip(), True


def run_opencode_reviewer(ticket_path, description):
    msg = (
        f"You are acting as a reviewer. Review the implemented ticket: {ticket_path.stem}\n\n"
        f"Description:\n{description}\n\n"
        f"Read the project source code in {PROJECT_DIR} to review the implementation.\n"
        f"Check git log and diff for the ticket/{ticket_path.stem} branch to see what changed.\n"
        f"Add a 'Review:' section at the end of the ticket file with your feedback.\n"
        f"If the ticket specification itself needs refinement, add your feedback and update its `stage` to 'draft_review'.\n"
        f"If the implementation needs fixes, update its `stage` to 'need_fix'.\n"
        f"If the implementation is correct and complete, update its `stage` to 'reviewed'."
    )
    log(f"Reviewer checking {ticket_path.name}...")
    r = subprocess.run(
        ["opencode", "run", "--dir", str(PROJECT_DIR), "--dangerously-skip-permissions", msg],
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        log(f"opencode failed: {r.stderr.strip()[-300:]}")
        return "", False
    log(f"opencode done")
    return ((r.stdout or "") + "\n" + (r.stderr or "")).strip(), True


def run_opencode_coder(ticket_path, description):
    msg = (
        f"Implement this ticket: {ticket_path.stem}\n\n"
        f"Description:\n{description}\n\n"
        f"Please perform the following:\n"
        f"1. Implement the necessary code changes in the project.\n"
        f"2. Add corresponding tests to verify the implementation.\n"
        f"3. Update documentation if necessary.\n"
        f"If the ticket description is unclear or incomplete, add a 'Comment:' section at the end of the file "
        f"explaining what's missing, then update its `stage` to 'draft_review'.\n"
        f"Otherwise, after completing the implementation, tests, and docs, comment implementation detail to ticket at {ticket_path}."
    )
    log(f"Coder implementing {ticket_path.name}...")
    r = subprocess.run(
        ["opencode", "run", "--dir", str(PROJECT_DIR), "--dangerously-skip-permissions", msg],
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        log(f"opencode failed: {r.stderr.strip()[-300:]}")
        return "", False
    log(f"opencode done")
    return ((r.stdout or "") + "\n" + (r.stderr or "")).strip(), True



def main():
    log(f"Agent started – polling every {POLL_INTERVAL}s")
    while True:
        # Admin role: refine drafts
        drafts = get_tickets("draft")
        if drafts:
            ticket_path = drafts[0]
            from_stage = get_stage(ticket_path)
            description = read_description(ticket_path)
            ensure_project()
            output, ok = run_opencode_admin(ticket_path, description)
            if ok:
                to_stage = "draft_review"
                set_stage(ticket_path, to_stage)
                git_commit_push(AGENT_REPO, f"{ticket_path.stem}: admin refined to {to_stage}")
                log_transition(ticket_path, "admin", from_stage, to_stage, "ok")
            else:
                log(f"Admin failed for {ticket_path.name}")
                log_transition(ticket_path, "admin", from_stage, from_stage, "failed", "opencode run failed")

        # Manager role: review refined tickets
        reviews = get_tickets("draft_review")
        if reviews:
            ticket_path = reviews[0]
            from_stage = get_stage(ticket_path)
            description = read_description(ticket_path)
            ensure_project()
            output, ok = run_opencode_manager(ticket_path, description)
            if ok:
                to_stage = get_stage(ticket_path)
                log(f"Manager set {ticket_path.name} to {to_stage}")
                git_commit_push(AGENT_REPO, f"{ticket_path.stem}: manager reviewed to {to_stage}")
                log_transition(ticket_path, "manager", from_stage, to_stage, "ok")
            else:
                log(f"Manager failed for {ticket_path.name}")
                log_transition(ticket_path, "manager", from_stage, from_stage, "failed", "opencode run failed")

        # Developer role: implement tasks
        for coder_stage in ("need_fix", "todo"):
            tickets = [t for t in get_tickets(coder_stage) if dependencies_satisfied(t)]
            if not tickets:
                continue
            ticket_path = tickets[0]
            from_stage = get_stage(ticket_path)
            description = read_description(ticket_path)

            claim_ticket(ticket_path)
            ensure_project()
            branch = create_ticket_branch(ticket_path.stem)
            output, ok = run_opencode_coder(ticket_path, description)

            if ok:
                new_stage = get_stage(ticket_path)
                if new_stage == "draft_review":
                    to_stage = "draft_review"
                    log(f"Coder returned {ticket_path.name} to {to_stage}")
                    git_commit_push(AGENT_REPO, f"{ticket_path.stem}: coder returned to {to_stage}")
                else:
                    to_stage = "need_review"
                    git_commit_push(PROJECT_DIR, f"Implement {ticket_path.stem}", branch)
                    finish_ticket(ticket_path)
                log_transition(ticket_path, "coder", from_stage, to_stage, "ok")
            else:
                to_stage = coder_stage
                log(f"Reverting {ticket_path.name} to {to_stage}")
                set_stage(ticket_path, to_stage)
                git_commit_push(AGENT_REPO, f"{ticket_path.stem}: revert to {to_stage}")
                log_transition(ticket_path, "coder", from_stage, to_stage, "failed", "opencode run failed")

        # Reviewer role: review implemented tickets
        need_reviews = get_tickets("need_review")
        if need_reviews:
            ticket_path = need_reviews[0]
            from_stage = get_stage(ticket_path)
            log(f"Claim {ticket_path.name} -> reviewing")
            set_stage(ticket_path, "reviewing")
            git_commit_push(AGENT_REPO, f"{ticket_path.stem}: move to reviewing")
            description = read_description(ticket_path)
            ensure_project()
            subprocess.run(["git", "fetch", "origin"], cwd=PROJECT_DIR, capture_output=True, text=True)
            output, ok = run_opencode_reviewer(ticket_path, description)
            if ok:
                to_stage = get_stage(ticket_path)
                log(f"Reviewer set {ticket_path.name} to {to_stage}")
                git_commit_push(AGENT_REPO, f"{ticket_path.stem}: reviewer {to_stage}")
                log_transition(ticket_path, "reviewer", "reviewing", to_stage, "ok")
            else:
                log(f"Reviewer failed for {ticket_path.name}")
                log_transition(ticket_path, "reviewer", "reviewing", "reviewing", "failed", "opencode run failed")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
