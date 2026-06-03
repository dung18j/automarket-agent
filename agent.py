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
STALE_TIMEOUT = 86400  # 24 hours


def log(msg):
    print(f"[agent] {msg}", flush=True)

def debug(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:15]
    print(f"[debug {ts}] {msg}", flush=True)


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


def set_front_matter_field(path, field, value):
    text = path.read_text()
    if re.search(rf"^{field}:", text, re.MULTILINE):
        text = re.sub(rf"^{field}:.*", f"{field}: {value}", text, flags=re.MULTILINE)
    else:
        text = re.sub(r"^(stage:.*)", rf"\1\n{field}: {value}", text, flags=re.MULTILINE)
    path.write_text(text)


def get_front_matter_field(path, field):
    m = re.search(rf"^{field}:\s*(\S+)", path.read_text(), re.MULTILINE)
    return m.group(1) if m else None


def remove_front_matter_field(path, field):
    text = path.read_text()
    text = re.sub(rf"^{field}:.*\n?", "", text, flags=re.MULTILINE)
    path.write_text(text)


def git_commit_push(repo, msg, branch=None):
    debug(f"git add -A in {repo}")
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True, text=True)
    debug("git diff --cached --quiet")
    r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo, capture_output=True)
    if r.returncode != 0:
        debug(f"git commit -m '{msg}'")
        subprocess.run(["git", "commit", "-m", msg], cwd=repo, capture_output=True, text=True)
    if branch:
        debug(f"git push -u origin {branch}")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=repo, capture_output=True, text=True)
    else:
        debug("git push")
        subprocess.run(["git", "push"], cwd=repo, capture_output=True, text=True)
    debug("git checkout main")
    subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True, text=True)
    debug("git_commit_push done")


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


def claim_ticket(ticket_path, new_stage):
    claimed_from = get_stage(ticket_path)
    log(f"Claim {ticket_path.name} -> {new_stage}")
    debug(f"set_stage {ticket_path.name} -> {new_stage}")
    set_stage(ticket_path, new_stage)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    set_front_matter_field(ticket_path, "claimed_at", now)
    set_front_matter_field(ticket_path, "claimed_from", claimed_from)
    git_commit_push(AGENT_REPO, f"Claim {ticket_path.stem}: {claimed_from} -> {new_stage}")


def unclaim_ticket(ticket_path):
    claimed_from = get_front_matter_field(ticket_path, "claimed_from") or "draft"
    log(f"Unclaim {ticket_path.name} (stale) -> {claimed_from}")
    set_stage(ticket_path, claimed_from)
    remove_front_matter_field(ticket_path, "claimed_at")
    remove_front_matter_field(ticket_path, "claimed_from")
    git_commit_push(AGENT_REPO, f"{ticket_path.stem}: unclaim (stale) -> {claimed_from}")


def clear_claim_meta(ticket_path):
    text = ticket_path.read_text()
    text = re.sub(r"^claimed_at:.*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^claimed_from:.*\n?", "", text, flags=re.MULTILINE)
    ticket_path.write_text(text)


def check_expired_claims():
    now = datetime.now(timezone.utc).timestamp()
    claimed_stages = {"draft_refining", "draft_reviewing", "doing", "reviewing"}
    for f in TICKET_DIR.glob("*.md"):
        stage = get_stage(f)
        if stage not in claimed_stages:
            continue
        claimed_at = get_front_matter_field(f, "claimed_at")
        if not claimed_at:
            continue
        try:
            claimed_ts = datetime.strptime(claimed_at, "%Y-%m-%dT%H:%M:%SZ").timestamp()
        except ValueError:
            continue
        if now - claimed_ts > STALE_TIMEOUT:
            log(f"Ticket {f.name} claimed at {claimed_at} (>24h), resetting")
            unclaim_ticket(f)


def finish_ticket(ticket_path):
    log(f"Finish {ticket_path.name} -> need_review")
    debug(f"set_stage {ticket_path.name} -> need_review")
    set_stage(ticket_path, "need_review")
    git_commit_push(AGENT_REPO, f"{ticket_path.stem}: move to need_review")


def send_comment(ticket_path, role, comment_text):
    text = ticket_path.read_text()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    comment_block = f"\n### {role} ({now})\n\n{comment_text}\n"
    if "## Conversation" in text:
        text = re.sub(r"(## Conversation\n)", rf"\1{comment_block}", text)
    else:
        text += f"\n## Conversation\n{comment_block}"
    ticket_path.write_text(text)
    git_commit_push(AGENT_REPO, f"{ticket_path.stem}: {role} comment")


def ensure_project():
    if not PROJECT_DIR.exists():
        log(f"Clone {PROJECT_REPO}")
        debug("cloning project repo")
        subprocess.run(["git", "clone", PROJECT_REPO, str(PROJECT_DIR)], capture_output=True, text=True)
    debug("git pull --rebase in project dir")
    subprocess.run(["git", "pull", "--rebase"], cwd=PROJECT_DIR, capture_output=True, text=True)
    debug("ensure_project done")


def create_ticket_branch(ticket_stem):
    branch = f"ticket/{ticket_stem}"
    log(f"Switching to branch {branch}")
    debug(f"git checkout main in project dir")
    subprocess.run(["git", "checkout", "main"], cwd=PROJECT_DIR, capture_output=True, text=True)
    debug(f"git branch -D {branch}")
    subprocess.run(["git", "branch", "-D", branch], cwd=PROJECT_DIR, capture_output=True, text=True)
    debug(f"git checkout -b {branch}")
    subprocess.run(["git", "checkout", "-b", branch], cwd=PROJECT_DIR, capture_output=True, text=True)
    debug("create_ticket_branch done")
    return branch

def run_opencode_admin(ticket_path, description):
    debug(f"run_opencode_admin START for {ticket_path.name}")
    msg = (
        f"You are acting as a admin. Refine the draft ticket: {ticket_path.stem}\n\n"
        f"Current Description:\n{description}\n\n"
        f"1. Read the project source code in {PROJECT_DIR} to understand the context.\n"
        f"2. If the task is complex, break it down into sub-tasks. For each sub-task, create a new ticket file in {TICKET_DIR} "
        f"with a descriptive filename like '{ticket_path.stem}-subtask-name.md'. Each sub-ticket must have front-matter with "
        f"'stage: todo'. Update the parent ticket's `depend_on` field to list all created sub-tickets.\n"
        f"3. Update the parent ticket file at {ticket_path} with detailed technical information and a clear step-by-step instruction for the developer.\n"
        f"4. Add a comment under the '## Conversation' section of {ticket_path} explaining what changes you made and why.\n"
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
    debug(f"run_opencode_admin END for {ticket_path.name} (rc={r.returncode})")
    return ((r.stdout or "") + "\n" + (r.stderr or "")).strip(), True


def run_opencode_manager(ticket_path, description):
    debug(f"run_opencode_manager START for {ticket_path.name}")
    msg = (
        f"You are acting as a manager. Review the refined ticket: {ticket_path.stem}\n\n"
        f"Description:\n{description}\n\n"
        f"Read the project source code in {PROJECT_DIR} to verify technical feasibility.\n"
        f"Then edit the ticket file at {ticket_path}:\n"
        f"- Change the `stage:` field in the front-matter (between --- lines) to `todo` "
        f"if the ticket has enough detail and clear instructions to be implemented.\n"
        f"- Change the `stage:` field to `draft` if the ticket needs more information or corrections.\n"
        f"- Add a comment under the '## Conversation' section of {ticket_path} explaining your decision.\n"
        f"The file uses front-matter format: ---\\nstage: <value>\\n---"
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
    debug(f"run_opencode_manager END for {ticket_path.name} (rc={r.returncode})")
    return ((r.stdout or "") + "\n" + (r.stderr or "")).strip(), True


def run_opencode_reviewer(ticket_path, description):
    debug(f"run_opencode_reviewer START for {ticket_path.name}")
    msg = (
        f"You are acting as a reviewer. Review the implemented ticket: {ticket_path.stem}\n\n"
        f"Description:\n{description}\n\n"
        f"Read the project source code in {PROJECT_DIR} to review the implementation.\n"
        f"Check git log and diff for the ticket/{ticket_path.stem} branch to see what changed.\n"
        f"Add a comment under the '## Conversation' section of {ticket_path} with your review feedback.\n"
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
    debug(f"run_opencode_reviewer END for {ticket_path.name} (rc={r.returncode})")
    return ((r.stdout or "") + "\n" + (r.stderr or "")).strip(), True


def run_opencode_coder(ticket_path, description):
    debug(f"run_opencode_coder START for {ticket_path.name}")
    msg = (
        f"Implement this ticket: {ticket_path.stem}\n\n"
        f"Description:\n{description}\n\n"
        f"Please perform the following:\n"
        f"1. Implement the necessary code changes in the project.\n"
        f"2. Add corresponding tests to verify the implementation.\n"
        f"3. Update documentation if necessary.\n"
        f"If the ticket description is unclear or incomplete, add a comment under the '## Conversation' section of {ticket_path} "
        f"explaining what's missing, then update its `stage` to 'draft_review'.\n"
        f"Otherwise, after completing the implementation, tests, and docs, add a comment under the '## Conversation' section "
        f"of {ticket_path} detailing what was implemented."
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
    debug(f"run_opencode_coder END for {ticket_path.name} (rc={r.returncode})")
    return ((r.stdout or "") + "\n" + (r.stderr or "")).strip(), True



def main():
    log(f"Agent started – polling every {POLL_INTERVAL}s")
    iteration = 0
    while True:
        iteration += 1
        debug(f"=== Iteration {iteration} START ===")
        check_expired_claims()

        debug("checking draft tickets")
        # Admin role: refine drafts
        drafts = get_tickets("draft")
        if drafts:
            ticket_path = drafts[0]
            from_stage = get_stage(ticket_path)
            claim_ticket(ticket_path, "draft_refining")
            description = read_description(ticket_path)
            ensure_project()
            output, ok = run_opencode_admin(ticket_path, description)
            if ok:
                to_stage = "draft_review"
                set_stage(ticket_path, to_stage)
                clear_claim_meta(ticket_path)
                git_commit_push(AGENT_REPO, f"{ticket_path.stem}: admin refined to {to_stage}")
                log_transition(ticket_path, "admin", from_stage, to_stage, "ok")
            else:
                log(f"Admin failed for {ticket_path.name}")
                log_transition(ticket_path, "admin", from_stage, from_stage, "failed", "opencode run failed")

        debug("checking draft_review tickets")
        # Manager role: review refined tickets
        reviews = get_tickets("draft_review")
        if reviews:
            ticket_path = reviews[0]
            from_stage = get_stage(ticket_path)
            claim_ticket(ticket_path, "draft_reviewing")
            description = read_description(ticket_path)
            ensure_project()
            output, ok = run_opencode_manager(ticket_path, description)
            if ok:
                to_stage = get_stage(ticket_path)
                if to_stage == "draft_reviewing":
                    log(f"Manager did not change stage for {ticket_path.name}, checking output for decision")
                    has_comment = bool(re.search(r"### \w+ \(\d{4}", ticket_path.read_text()))
                    to_stage = "draft" if has_comment else "todo"
                set_stage(ticket_path, to_stage)
                clear_claim_meta(ticket_path)
                log(f"Manager set {ticket_path.name} to {to_stage}")
                git_commit_push(AGENT_REPO, f"{ticket_path.stem}: manager reviewed to {to_stage}")
                log_transition(ticket_path, "manager", from_stage, to_stage, "ok")
            else:
                log(f"Manager failed for {ticket_path.name}")
                log_transition(ticket_path, "manager", from_stage, from_stage, "failed", "opencode run failed")

        debug("checking need_fix/todo tickets")
        # Developer role: implement tasks
        for coder_stage in ("need_fix", "todo"):
            tickets = [t for t in get_tickets(coder_stage) if dependencies_satisfied(t)]
            if not tickets:
                continue
            ticket_path = tickets[0]
            from_stage = get_stage(ticket_path)
            description = read_description(ticket_path)

            claim_ticket(ticket_path, "doing")
            ensure_project()
            branch = create_ticket_branch(ticket_path.stem)
            output, ok = run_opencode_coder(ticket_path, description)

            if ok:
                new_stage = get_stage(ticket_path)
                if new_stage == "draft_review":
                    to_stage = "draft_review"
                    log(f"Coder returned {ticket_path.name} to {to_stage}")
                    clear_claim_meta(ticket_path)
                    git_commit_push(AGENT_REPO, f"{ticket_path.stem}: coder returned to {to_stage}")
                else:
                    to_stage = "need_review"
                    clear_claim_meta(ticket_path)
                    git_commit_push(PROJECT_DIR, f"Implement {ticket_path.stem}", branch)
                    finish_ticket(ticket_path)
                log_transition(ticket_path, "coder", from_stage, to_stage, "ok")
            else:
                to_stage = coder_stage
                log(f"Reverting {ticket_path.name} to {to_stage}")
                set_stage(ticket_path, to_stage)
                git_commit_push(AGENT_REPO, f"{ticket_path.stem}: revert to {to_stage}")
                log_transition(ticket_path, "coder", from_stage, to_stage, "failed", "opencode run failed")

        debug("checking need_review tickets")
        # Reviewer role: review implemented tickets
        need_reviews = get_tickets("need_review")
        if need_reviews:
            ticket_path = need_reviews[0]
            from_stage = get_stage(ticket_path)
            claim_ticket(ticket_path, "reviewing")
            description = read_description(ticket_path)
            ensure_project()
            subprocess.run(["git", "fetch", "origin"], cwd=PROJECT_DIR, capture_output=True, text=True)
            output, ok = run_opencode_reviewer(ticket_path, description)
            if ok:
                to_stage = get_stage(ticket_path)
                clear_claim_meta(ticket_path)
                log(f"Reviewer set {ticket_path.name} to {to_stage}")
                git_commit_push(AGENT_REPO, f"{ticket_path.stem}: reviewer {to_stage}")
                log_transition(ticket_path, "reviewer", "reviewing", to_stage, "ok")
            else:
                log(f"Reviewer failed for {ticket_path.name}")
                log_transition(ticket_path, "reviewer", "reviewing", "reviewing", "failed", "opencode run failed")

        debug(f"sleeping {POLL_INTERVAL}s")
        time.sleep(POLL_INTERVAL)
        debug(f"woke up")


if __name__ == "__main__":
    main()
