---
stage: draft_review
---

# Title: Update README with current project status

## Description

Update README.md to accurately reflect the current project state. The existing 90-line README covers basics (architecture tree, quick start, crate table) but is missing significant features, documentation references, and configuration details.

## Changes Required

### 1. Update Architecture Section
- Keep the ASCII tree but add **PostgreSQL** recording in `automarket-record` description (currently only says "JSONL files")
- Mention feature flags: `automarket-record` has a `pg` feature for PostgreSQL support via `sqlx`

### 2. Expand Quick Start Section
- Add **Prerequisites**: mention PostgreSQL (optional, for `pg` feature), WASM target `wasm32-unknown-unknown` for browser UI
- Add **Setup**: reference `rust-toolchain.toml` for toolchain, note that `.env.example` does not exist yet — instruct user to create `.env` manually with these vars:
  ```
  DNSE_API_KEY=your_api_key
  DNSE_API_SECRET=your_api_secret
  STOCK_SYMBOL=HPG
  STOCK_DATA_DIR=stock_data
  ```
- Add **Feature flags**: explain how to enable PostgreSQL recording with `--features pg`
- Add **Browser UI** instructions with the correct `trunk serve` command (currently relative `cd automarket-browser` but `trunk` must be installed)
- Add **Devcontainer** note: `.devcontainer/` provides a preconfigured Docker environment for development

### 3. Add Features Section (new)
List key capabilities:
- **Real-time WebSocket market data** — trades, quotes, OHLC bars, order/position events from DNSE
- **Data recording** — JSONL files per symbol (default) or PostgreSQL via `pg` feature
- **P2P monitoring** — iroh-based remote ping endpoint
- **REST API SDK** — all 24 DNSE API endpoints (accounts, orders, market data, broker)
- **Browser UI** — Dioxus WASM app that pings the daemon over iroh

### 4. Add Documentation Reference (new)
Add a section pointing to `docs/`:
- `docs/crate-structure.md` — crate dependency graph
- `docs/websocket-module.md` — WebSocket module architecture
- `docs/api-test-suite.md` — API endpoint reference and test specs
- `docs/project-rules.md` — project conventions

### 5. Expand Crates Table
Clarify the `Bot` trait mentioned in `automarket-trait` — note it requires implementing `handle_trade`, `handle_ohlc`, `handle_quote` methods.

### 6. Update Development Section
- Add link to `rfcs/` for RFC process
- Add testing instructions: `cargo test --workspace`
- Add formatting: `cargo fmt`
- Add linting: `cargo clippy --workspace`

## Step-by-Step Instructions

1. Read `docs/crate-structure.md`, `docs/automarket-trait.md`, `docs/automarket-record.md`, `docs/automarket-iroh.md`, `docs/automarket-runner.md`, `docs/websocket-module.md`, `docs/api-test-suite.md`, `docs/project-rules.md` for accurate descriptions
2. Read `CHANGELOG.md` to incorporate key unreleased/recent changes
3. Read `automarket-runner/src/main.rs` to confirm env var names and default values
4. Update `README.md` with changes listed above
5. `cargo fmt` to ensure no formatting issues
6. Verify by reading the updated file

## Notes

- No `.env.example` exists in the repo — do not create one (out of scope), but note this in setup instructions
- The browser UI instructions should mention installing `trunk` via `cargo install trunk`
- Check that the architecture tree diagram aligns with the actual crate dependency graph in `docs/crate-structure.md`
