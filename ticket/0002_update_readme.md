---
# Possible stages: draft | todo | doing | need_review | reviewing | need_fix | done | rejected
stage: need_review
---

# Title: Update README with current project status

## Description

Update the README.md to reflect the current project status, including the agent's functionality, architecture, and setup instructions. Ensure it accurately describes what the project does and how to use it.

## Conversation

_opencode comment @ 2026-06-03 04:43:54_

Now I understand the task. The reviewer noted that all agent-related content should be removed from README. The current README still has a "## Development" section referencing AGENTS.md. Let me fix this.
The remote already has the fix implemented (commit `8c0da27` removed agent-driven development workflow from README per reviewer feedback). Let me verify the README is correct and update the ticket stage.
Done. The implementation was already on the remote branch via commit `8c0da27`, which stripped the Development, RFC Process, Merge Policy, and contributor-facing sections from README.md per reviewer feedback. I rebased locally, verified the README and CHANGELOG are correct, created `.agent/ticket.md` with stage `need_review`, and pushed.

[0m
> build · big-pickle
[0m
[0m→ [0mRead .
[0m✗ [0mRead .agent failed
[91m[1mError: [0mFile not found: /tmp/opencode/automarket/.agent
[0m→ [0mRead README.md
[0m
[0m$ [0mgit branch -a
main
* ticket/0002_update_readme
  remotes/origin/HEAD -> origin/main
  remotes/origin/agents
  remotes/origin/chore/remove-automarket-message
  remotes/origin/feat/remove-automarket-message
  remotes/origin/main
  remotes/origin/ticket/0002_update_readme
[0m
[0m→ [0mRead CHANGELOG.md
[0m
[0m$ [0mgit status
On branch ticket/0002_update_readme
nothing to commit, working tree clean
[0m
[0m$ [0mgit log --oneline -10
db0967f Implement 0002_update_readme
df5e6b8 install python3 in devcontainer
168179b chore: remove automarket-message source files and add crate structure docs
4e5acdc docs: switch RFC tracking from PRs to branches
1f426c8 docs: add RFC Steward Bot section to AGENTS.md
e1954d3 feat: add RFC template
cdcac35 Add ping() convenience function with RTT measurement
3d5e286 ticket agent development
7a68301 add devpod for project
0877df9 chore: remove unused automarket-message crate
[0m
[0m$ [0mgit show db0967f --stat
commit db0967f45bdb6822b799d554826e3640a5591ece
Author: Phạm Văn Dũng <dung18j@gmail.com>
Date:   Wed Jun 3 04:19:36 2026 +0000

    Implement 0002_update_readme

 README.md | 92 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-----
 1 file changed, 85 insertions(+), 7 deletions(-)
[0m
[0m$ [0mgit show db0967f
commit db0967f45bdb6822b799d554826e3640a5591ece
Author: Phạm Văn Dũng <dung18j@gmail.com>
Date:   Wed Jun 3 04:19:36 2026 +0000

    Implement 0002_update_readme

diff --git a/README.md b/README.md
index b467b91..d489429 100644
--- a/README.md
+++ b/README.md
@@ -1,12 +1,90 @@
-# auto-stock
-Stock auto trading
+# automarket
 
-For agent-driven development workflow, see `AGENTS.md`.
+Automated stock trading system for the Vietnamese market (DNSE exchange). Streams real-time market data, records trades/OHLC/quotes, and provides a P2P monitoring interface.
 
-## Merge Policy
+## Architecture
 
-This repository uses **squash merge** as the merge strategy. All commits on a feature branch will be squashed into a single commit when merging into `main`.
+```
+automarket-runner     # Server binary — connects to DNSE WebSocket, records data, exposes iroh P2P endpoint
+├── automarket-dnse   # DNSE REST API & WebSocket SDK — HMAC signing, 24 endpoints, streaming market data
+├── automarket-trait  # Core types: Trade, Ohlc, Quote, MarketItem, Bot trait
+├── automarket-record # Trade/OHLC recording and replay (JSONL files + PostgreSQL)
+├── automarket-iroh   # iroh P2P protocol — ping handler and ALPN
+└── automarket-browser # Dioxus web UI — browser-based ping client
+```
 
-## Changelog
+## Quick Start
 
-All notable changes must be documented in `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) format. Every commit should include a changelog entry describing the change. 
+### Prerequisites
+
+- Rust toolchain (see `rust-toolchain.toml`)
+- A DNSE trading account with API credentials
+
+### Setup
+
+1. Clone the repo and copy the example environment file:
+
+```bash
+git clone <repo-url>
+cd automarket
+cp .env.example .env
+```
+
+2. Fill in your DNSE credentials in `.env`:
+
+```
+DNSE_API_KEY=your_api_key
+DNSE_API_SECRET=your_api_secret
+STOCK_SYMBOL=HPG
+STOCK_DATA_DIR=stock_data
+```
+
+3. Run the daemon:
+
+```bash
+cargo run -p automarket-runner
+```
+
+The daemon connects to DNSE, subscribes to market data for the configured symbol, records it to `stock_data/`, and exposes an iroh P2P endpoint for remote monitoring.
+
+4. (Optional) Open the browser UI:
+
+```bash
+cd automarket-browser
+trunk serve --open
+```
+
+Enter the relay URL and endpoint ID printed by the daemon, then click **Ping Daemon**.
+
+### Examples
+
+Each crate has example binaries. Run them with:
+
+```bash
+cargo run --example <example_name> -p automarket-dnse
+```
+
+Examples include: `get_accounts`, `put_order`, `market_data_ws`, `get_ohlc`, and more (24 REST API endpoints plus WebSocket streaming).
+
+## Crates
+
+| Crate | Description |
+|---|---|
+| `automarket-trait` | Core types — `Trade`, `Ohlc`, `Quote`, `MarketItem` enum, `Bot` trait |
+| `automarket-record` | Recording/replay to JSONL files and PostgreSQL via `sqlx` |
+| `automarket-iroh` | iroh P2P ping protocol — `PingProtocol` handler and `ALPN` constant |
+| `automarket-runner` | Server binary — connects to DNSE WebSocket, records market data, runs iroh P2P endpoint |
+| `automarket-dnse` | DNSE REST API & WebSocket SDK — HMAC-SHA256 signing, 24 API methods, streaming market data |
+| `automarket-browser` | Dioxus web UI — browser-based iroh ping client (WASM) |
+
+## Development
+
+For the agent-driven development workflow, see `AGENTS.md`.
+
+### Merge Policy
+
+This repository uses **squash merge**. All commits on a feature branch are squashed into a single commit when merging into `main`.
+
+### Changelog
+
+All notable changes are documented in `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) format.
[0m
[0m$ [0mgit show origin/ticket/0002_update_readme:.agent/ticket.md 2>/dev/null || echo "No .agent/ticket.md"
No .agent/ticket.md
[0m
[0m$ [0mgit show origin/ticket/0002_update_readme:.agent/description.md 2>/dev/null || echo "No .agent/description.md"
No .agent/description.md
[0m
[0m$ [0mgit show origin/ticket/0002_update_readme:.agent/notes.md 2>/dev/null || echo "No .agent/notes.md"
No .agent/notes.md
[0m
[0m# [0mTodos
[•] Pull origin/main to get latest state
[ ] Remove agent-related content from README.md (Development section, Merge Policy, Changelog)
[ ] Update CHANGELOG.md
[ ] Update .agent/ticket.md stage to need_review, commit, and push
[0m
[0m$ [0mgit pull origin main
From github.com:dung18j/automarket
 * branch            main       -> FETCH_HEAD
Already up to date.
[0m
[0m$ [0mgit fetch origin ticket/0002_update_readme && git log --oneline origin/ticket/0002_update_readme -5
From github.com:dung18j/automarket
 * branch            ticket/0002_update_readme -> FETCH_HEAD
8c0da27 docs: remove agent-driven development workflow from README
256bf4a docs: update README with documentation links, testing instructions, and workflow details
db0967f Implement 0002_update_readme
df5e6b8 install python3 in devcontainer
168179b chore: remove automarket-message source files and add crate structure docs
[0m
[0m$ [0mgit log --oneline ticket/0002_update_readme..origin/ticket/0002_update_readme
8c0da27 docs: remove agent-driven development workflow from README
256bf4a docs: update README with documentation links, testing instructions, and workflow details
[0m
[0m$ [0mgit rebase origin/ticket/0002_update_readme
Successfully rebased and updated refs/heads/ticket/0002_update_readme.
[0m
[0m# [0mTodos
[✓] Pull origin/main to get latest state
[•] Remove agent-related content from README.md (Development section, Merge Policy, Changelog)
[ ] Update CHANGELOG.md
[ ] Update .agent/ticket.md stage to need_review, commit, and push
[0m
[0m→ [0mRead README.md
[0m
[0m$ [0mgit show origin/ticket/0002_update_readme:README.md 2>/dev/null || echo "no remote"
# automarket

Automated stock trading system for the Vietnamese market (DNSE exchange). Streams real-time market data, records trades/OHLC/quotes, and provides a P2P monitoring interface.

## Architecture

```
automarket-runner     # Server binary — connects to DNSE WebSocket, records data, exposes iroh P2P endpoint
├── automarket-dnse   # DNSE REST API & WebSocket SDK — HMAC signing, 24 endpoints, streaming market data
├── automarket-trait  # Core types: Trade, Ohlc, Quote, MarketItem, Bot trait
├── automarket-record # Trade/OHLC recording and replay (JSONL files + PostgreSQL)
├── automarket-iroh   # iroh P2P protocol — ping handler and ALPN
└── automarket-browser # Dioxus web UI — browser-based ping client
```

## Quick Start

### Prerequisites

- Rust toolchain (see `rust-toolchain.toml`)
- A DNSE trading account with API credentials

### Setup

1. Clone the repo:

```bash
git clone <repo-url>
cd automarket
```

2. Create a `.env` file in the project root with your DNSE credentials:

```
DNSE_API_KEY=your_api_key
DNSE_API_SECRET=your_api_secret
STOCK_SYMBOL=HPG
STOCK_DATA_DIR=stock_data
```

3. Run the daemon:

```bash
cargo run -p automarket-runner
```

The daemon connects to DNSE, subscribes to market data for the configured symbol, records it to `stock_data/`, and exposes an iroh P2P endpoint for remote monitoring.

4. (Optional) Open the browser UI:

```bash
cd automarket-browser
trunk serve --open
```

Enter the relay URL and endpoint ID printed by the daemon, then click **Ping Daemon**.

### Examples

Each crate has example binaries. Run them with:

```bash
cargo run --example <example_name> -p automarket-dnse
```

Examples include: `get_accounts`, `put_order`, `market_data_ws`, `get_ohlc`, and more (24 REST API endpoints plus WebSocket streaming).

### Testing

Run all workspace tests:

```bash
cargo test --workspace
```

Run tests for a specific crate:

```bash
cargo test -p automarket-dnse
```

## Crates

| Crate | Description |
|---|---|
| `automarket-trait` | Core types — `Trade`, `Ohlc`, `Quote`, `MarketItem` enum, `Bot` trait |
| `automarket-record` | Recording/replay to JSONL files and PostgreSQL via `sqlx` |
| `automarket-iroh` | iroh P2P ping protocol — `PingProtocol` handler and `ALPN` constant |
| `automarket-runner` | Server binary — connects to DNSE WebSocket, records market data, runs iroh P2P endpoint |
| `automarket-dnse` | DNSE REST API & WebSocket SDK — HMAC-SHA256 signing, 24 API methods, streaming market data |
| `automarket-browser` | Dioxus web UI — browser-based iroh ping client (WASM) |

## Documentation

Detailed documentation for each crate and component is available in the [`docs/`](docs/) directory:

| Document | Description |
|---|---|
| [`crate-structure.md`](docs/crate-structure.md) | Workspace crate overview |
| [`automarket-trait.md`](docs/automarket-trait.md) | Core types, `MarketItem` enum, and `Bot` trait |
| [`automarket-record.md`](docs/automarket-record.md) | Trade/OHLC recording and replay (JSONL + PostgreSQL) |
| [`automarket-iroh.md`](docs/automarket-iroh.md) | iroh P2P ping protocol |
| [`automarket-runner.md`](docs/automarket-runner.md) | Server binary configuration and usage |
| [`websocket-module.md`](docs/websocket-module.md) | WebSocket streaming market data |
| [`api-test-suite.md`](docs/api-test-suite.md) | DNSE API test suite specification |

See [`CHANGELOG.md`](CHANGELOG.md) for release history.
[0m
[0m$ [0mgit show 8c0da27 --stat
commit 8c0da27e45709c4476321afe3a328969c5ddc2f3
Author: Phạm Văn Dũng <dung18j@gmail.com>
Date:   Wed Jun 3 11:36:27 2026 +0700

    docs: remove agent-driven development workflow from README
    
    Strips the Development, RFC Process, Merge Policy, and contributor-
    facing sections per reviewer feedback. Keeps project overview,
    architecture, quick start, testing, crate descriptions, and
    documentation references. Retains a brief changelog link.

 CHANGELOG.md |  3 +--
 README.md    | 25 +------------------------
 2 files changed, 2 insertions(+), 26 deletions(-)
[0m
[0m$ [0mgit show 256bf4a --stat
commit 256bf4af23152f886878a08f359fb85f9c94b178
Author: Phạm Văn Dũng <dung18j@gmail.com>
Date:   Wed Jun 3 04:27:45 2026 +0000

    docs: update README with documentation links, testing instructions, and workflow details

 CHANGELOG.md |  1 +
 README.md    | 50 +++++++++++++++++++++++++++++++++++++++++++++-----
 2 files changed, 46 insertions(+), 5 deletions(-)
[0m
[0m$ [0mgit show 8c0da27
commit 8c0da27e45709c4476321afe3a328969c5ddc2f3
Author: Phạm Văn Dũng <dung18j@gmail.com>
Date:   Wed Jun 3 11:36:27 2026 +0700

    docs: remove agent-driven development workflow from README
    
    Strips the Development, RFC Process, Merge Policy, and contributor-
    facing sections per reviewer feedback. Keeps project overview,
    architecture, quick start, testing, crate descriptions, and
    documentation references. Retains a brief changelog link.

diff --git a/CHANGELOG.md b/CHANGELOG.md
index 7537cba..181da24 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -2,10 +2,9 @@
 
 ## [Unreleased]
 
-- **docs**: Updated README.md with a Documentation section linking to crate docs, Testing instructions, improved Quick Start (removed defunct `.env.example` reference), expanded Development section with guidelines and opencode workflow details, and added RFC Process reference.
+- **docs**: Removed agent-driven development workflow documentation from README.md. Stripped Development, RFC Process, Merge Policy, and contributor-facing sections. Kept project overview, architecture, quick start, testing, crate descriptions, and documentation references.
 - **automarket-iroh**: Added `ping()` client convenience function that opens a bi-directional stream, sends `b"ping"`, waits for `b"pong"`, and returns the round-trip time as a `Duration`. Added `PingError` enum for typed error reporting. Updated `docs/automarket-iroh.md` and `docs/automarket-runner.md` documenting the feature.
 - **automarket-runner**: Updated `ping_client` example to use the new `automarket_iroh::ping::ping()` function.
-- **docs**: Moved agent-driven development workflow from README.md to AGENTS.md. Created `.agent/ticket.md` for ticket-based feature tracking with lifecycle stages (todo → doing → need_review → reviewing → need_fix → done). The `.agent/` directory is branch-local and removed before merging to `main`.
 
 - **automarket-message**: Removed unused crate (Ping/Pong Message enum, never imported elsewhere).
 
diff --git a/README.md b/README.md
index ebc02ef..15fe487 100644
--- a/README.md
+++ b/README.md
@@ -104,27 +104,4 @@ Detailed documentation for each crate and component is available in the [`docs/`
 | [`websocket-module.md`](docs/websocket-module.md) | WebSocket streaming market data |
 | [`api-test-suite.md`](docs/api-test-suite.md) | DNSE API test suite specification |
 
-### RFC Process
-
-Significant changes follow the RFC process. See [`rfcs/`](rfcs/) for active and archived proposals.
-
-## Development
-
-This project uses an agent-driven development workflow managed by [opencode](https://opencode.ai). See `AGENTS.md` for workflow rules.
-
-Every feature has a corresponding ticket in `.agent/ticket.md` with a lifecycle stage (todo → doing → need_review → reviewing → need_fix → done).
-
-### Guidelines
-
-- Create a feature branch from `main` for every change.
-- Never commit directly to `main`.
-- Every change includes documentation updates and changelog entries.
-- Branch names follow `type/description` (e.g., `feat/add-widget`).
-
-### Merge Policy
-
-This repository uses **squash merge**. All commits on a feature branch are squashed into a single commit when merging into `main`.
-
-### Changelog
-
-All notable changes are documented in [`CHANGELOG.md`](CHANGELOG.md) following the [Keep a Changelog](https://keepachangelog.com/) format. 
+See [`CHANGELOG.md`](CHANGELOG.md) for release history.
[0m
[0m$ [0mgit log --oneline --all -- .agent/ 2>/dev/null || echo "No .agent/ commits"
52f64c5 chore: create ticket to remove unused automarket-message crate
[0m
[0m$ [0mgit log --oneline origin/ticket/0002_update_readme
8c0da27 docs: remove agent-driven development workflow from README
256bf4a docs: update README with documentation links, testing instructions, and workflow details
db0967f Implement 0002_update_readme
df5e6b8 install python3 in devcontainer
168179b chore: remove automarket-message source files and add crate structure docs
4e5acdc docs: switch RFC tracking from PRs to branches
1f426c8 docs: add RFC Steward Bot section to AGENTS.md
e1954d3 feat: add RFC template
cdcac35 Add ping() convenience function with RTT measurement
3d5e286 ticket agent development
7a68301 add devpod for project
0877df9 chore: remove unused automarket-message crate
2f7e7f1 feat: rename ping ALPN from auto-stock/ping/0 to automarket/ping/0
cc486a2 feat: extract iroh protocols into automarket-iroh crate, use Router API
8102034 refactor: rename all crates to automarket-* prefix
5a6144b chore: add browser-ui/dist/ to .gitignore
4f55077 feat: add browser-ui crate — Dioxus + iroh in-browser ping UI
728d92c chore: rename stock_daemon directory to daemon
6ffed0e feat: replace Unix socket IPC with iroh P2P
4897904 feat: add Unix socket ping/pong IPC to stock-daemon with example client
05020f4 feat: add stock-daemon for recording single-symbol market data to JSONL
2e72efe fix: handle MarketItem::Quote variant in record crate match arms
cc41631 refactor: move PostgreSQL recorder into record crate behind pg feature gate
c8121f5 feat: add pg-record crate with PostgreSQL recorder via sqlx
022b516 Add Quote and QuoteData traits for top-of-book bid/ask quotes
2b9e466 style: cargo fmt
47e7f8a chore: add stock_data/ to gitignore
c784292 feat(record): add record_file module for per-symbol recording/replay
920d7a6 refactor(bot-trait): migrate to async Stream-based API
7d3dea5 Add cargo fmt rule to AGENTS.md and apply formatting
e7c2b90 Fix WebSocket keep-alive by sending JSON ping every 25 seconds
d2adf91 Add market data WebSocket example and fix SDK model deserialization
e32979d Enhance record crate with error types, lazy replay, passthrough recording, and time-range seeking
6455025 Add bot-trait and record crates with workspace Cargo.toml
a63d3a2 Enable WebSocket market data receiver module
7e1ba86 update agents.md
70435b8 Add 26 usage examples for DNSE REST API endpoints
3ab652b Add Rust DNSE SDK with full REST API coverage and snapshot tests
af4e0c6 Add opencode project configuration with workflow rules
a8b6ca2 Initial commit
[0m
[0m$ [0mgit status
On branch ticket/0002_update_readme
nothing to commit, working tree clean
[0m
[0m$ [0mgit log --all --diff-filter=A --name-only --format="" -- .agent/ticket.md .agent/description.md .agent/notes.md
.agent/description.md
.agent/ticket.md
[0m
[0m$ [0mdiff <(git show origin/ticket/0002_update_readme:README.md) README.md
(no output)
[0m
[0m$ [0mmkdir -p .agent
(no output)
[0m
[0m← [0mWrite .agent/ticket.md
Wrote file successfully.
[0m
[0m← [0mWrite .agent/description.md
Wrote file successfully.
[0m
[0m→ [0mRead CHANGELOG.md[90m [limit=15][0m
[0m
[0m$ [0mgit add .agent/ && git commit -m "Set ticket stage to need_review" && git push origin ticket/0002_update_readme
[ticket/0002_update_readme 64d5d40] Set ticket stage to need_review
 2 files changed, 10 insertions(+)
 create mode 100644 .agent/description.md
 create mode 100644 .agent/ticket.md
To github.com:dung18j/automarket.git
   8c0da27..64d5d40  ticket/0002_update_readme -> ticket/0002_update_readme
[0m
[0m# [0mTodos
[✓] Pull origin/main to get latest state
[✓] Remove agent-related content from README.md (Development section, Merge Policy, Changelog)
[✓] Update CHANGELOG.md
[✓] Update .agent/ticket.md stage to need_review, commit, and push
[0m

<!--
Agents can leave notes here for each other during the ticket lifecycle.
Use this for context that doesn't fit in the metadata (e.g., debating
about content, explaining why a change was rejected, clarifying
requirements, suggesting an approach).
-->

reviewer: remove all agent related document on readme. the project don't care who contributors are,
reviewer: implementer have to comment to ticket
