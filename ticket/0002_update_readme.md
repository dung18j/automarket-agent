---
stage: todo
depends_on: []
---

# Title: Update README with current project status

## Description

Update README.md to accurately reflect the current project state. The current README (107 lines) already has architecture tree, quick start, crate table, and documentation links, but is missing a dedicated Features section, detailed feature flag instructions, devcontainer note, browser UI prerequisites, RFC process reference, and development workflow commands.

## Changes Required

### 1. Update Architecture Section
- Keep the ASCII tree. Verify PostgreSQL is mentioned in `automarket-record` description — currently reads `"Trade/OHLC recording and replay (JSONL files + PostgreSQL)"` (line 11). This is correct, no change needed.
- Add mention that `automarket-record` has a `pg` feature (gated behind `--features pg`). Could add a footnote or inline note near the tree.

### 2. Expand Quick Start Section
The Quick Start already has **Prerequisites** and **Setup** sub-sections but needs:

- **Prerequisites**: Add mention of WASM target `wasm32-unknown-unknown` for browser UI, and PostgreSQL (optional, for `pg` feature)
- **Setup**: already references `.env` creation with correct vars. Add note that `rust-toolchain.toml` pins the toolchain and includes `wasm32-unknown-unknown` target.
- **Feature flags**: new sub-section explaining `--features pg` for PostgreSQL recording via `sqlx`
- **Browser UI**: expand existing instructions. Mention `trunk` must be installed via `cargo install trunk`. Fix the relative path issue in the current instructions (currently `cd automarket-browser` — confirm it's correct when run from project root).
- **Devcontainer**: new sub-section noting `.devcontainer/` provides a preconfigured Docker+VSCode environment (rust-analyzer, TOML formatter, LLDB, cargo-on-wasm32)

### 3. Add Features Section (new)
Insert a new section after Quick Start listing key capabilities:

- **Real-time WebSocket market data** — trades, quotes, OHLC bars, order/position events, market indices, foreign investor activity from DNSE
- **Data recording** — JSONL files per symbol (default) or PostgreSQL via `pg` feature (requires `DATABASE_URL` env)
- **P2P monitoring** — iroh-based remote ping endpoint (`automarket/ping/0` ALPN)
- **REST API SDK** — all 24 DNSE API endpoints (accounts, orders, market data, broker) with HMAC-SHA256 signing
- **Browser UI** — Dioxus WASM app that pings the daemon over iroh

### 4. Documentation Reference (already partially exists)
The README already has a **Documentation** section (lines 93-107) with a table. Verify all docs are listed:
- `docs/crate-structure.md` — workspace crate overview ✓ (exists)
- `docs/automarket-trait.md` — core types, `MarketItem` enum, `Bot` trait ✓
- `docs/automarket-record.md` — recording/replay (JSONL + PostgreSQL) ✓
- `docs/automarket-iroh.md` — iroh P2P ping protocol ✓
- `docs/automarket-runner.md` — server binary configuration ✓
- `docs/websocket-module.md` — WebSocket module architecture ✓
- `docs/api-test-suite.md` — DNSE API endpoint reference and test specs ✓
- `docs/project-rules.md` — project conventions ✗ (NOT currently listed — **add this**)

### 5. Expand Crates Table
**⚠️ FIX FACTUAL ERROR**: The draft claims `Bot` requires `handle_trade`, `handle_ohlc`, `handle_quote`. This is **wrong**. The `Bot` trait in `automarket-trait/src/lib.rs` requires:
- `fn symbol(&self) -> &str`
- `fn interval(&self) -> &str`  
- `impl Stream<Item = MarketItem> + Unpin`

The three types (`Trade`, `Ohlc`, `Quote`) are **variants** of the `MarketItem` enum — users pattern-match on them, not implement handler methods.

Update the crate description in the table accordingly:
```
| `automarket-trait` | Core types — `Trade`, `Ohlc`, `Quote`, `MarketItem` enum, `Bot` trait (`Stream<Item=MarketItem>` + `symbol()`/`interval()`) |
```

### 6. Add Development Section (new)
After the Crates table, add a **Development** section:

- **RFC Process**: link to `rfcs/` for proposing design changes
- **Testing**: `cargo test --workspace`
- **Formatting**: `cargo fmt`
- **Linting**: `cargo clippy --workspace`

## Step-by-Step Instructions

1. Read the current `README.md` to understand what already exists
2. Read these docs for accurate descriptions: `docs/crate-structure.md`, `docs/automarket-trait.md`, `docs/automarket-record.md`, `docs/automarket-iroh.md`, `docs/automarket-runner.md`, `docs/websocket-module.md`, `docs/api-test-suite.md`, `docs/project-rules.md`
3. Read `automarket-runner/src/main.rs` to confirm env var names (`DNSE_API_KEY`, `DNSE_API_SECRET`, `STOCK_SYMBOL` default `HPG`, `STOCK_DATA_DIR` default `stock_data`)
4. Read `automarket-trait/src/lib.rs` to verify `Bot` trait definition (confirm no handler methods — only `symbol()`, `interval()`, `Stream<Item=MarketItem>`)
5. Read `automarket-browser/README.md` for accurate browser UI instructions
6. Read `.devcontainer/devcontainer.json` for devcontainer details
7. Implement changes:
   - Section 1: Verify PostgreSQL mention is present (it is), add feature flag inline note
   - Section 2: Expand Prerequisites (WASM target, PostgreSQL), add Feature Flags sub-section, update Browser UI instructions, add Devcontainer note
   - Section 3: Create new Features section between Quick Start and the Crates table
   - Section 4: Add `docs/project-rules.md` to the Documentation table
   - Section 5: Fix `Bot` trait description in Crates table (remove handler method references)
   - Section 6: Create new Development section after Crates table
8. `cargo fmt` to ensure no formatting issues
9. Verify by reading the updated file

## Notes

- No `.env.example` exists in the repo — **do not create one** (out of scope). The setup instructions already tell users to create `.env` manually.
- The browser UI instructions should mention installing `trunk` via `cargo install trunk` (already in `automarket-browser/README.md`).
- Verify that the architecture tree diagram aligns with the actual crate dependency graph in `docs/crate-structure.md`. Both should list the same 6 crates.
- The Documentation table should reference `CHANGELOG.md` as it already does (line 107).
- Keep the existing tone and style — concise, direct, minimal markdown.
- Do not add emojis.
