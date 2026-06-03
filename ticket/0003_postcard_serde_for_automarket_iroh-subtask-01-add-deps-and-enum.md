---
stage: todo
parent: 0003_postcard_serde_for_automarket_iroh
---

# Subtask: Add serde/postcard deps and PingMessage enum

## Description

Add `serde` + `postcard` dependencies to `automarket-iroh/Cargo.toml` and create `src/protocol.rs` with the `PingMessage` enum. Register the new module in `src/lib.rs`.

## Changes Required

### 1. Update `automarket-iroh/Cargo.toml`

Append to `[dependencies]`:
```toml
serde = { version = "1", features = ["derive"] }
postcard = { version = "1", default-features = false }
```

### 2. Create `automarket-iroh/src/protocol.rs`

```rust
use serde::{Deserialize, Serialize};

/// Ping/pong protocol messages serialized with postcard.
#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PingMessage {
    Ping,
    Pong,
    Unknown,
}
```

Note: `PartialEq` + `Eq` are required for test assertions.

### 3. Register module in `automarket-iroh/src/lib.rs`

```rust
pub mod ping;
pub mod protocol;
```

Add after the existing `pub mod ping;` line.

## Files to Modify

- `automarket-iroh/Cargo.toml` — add 2 dependencies
- `automarket-iroh/src/lib.rs` — add `pub mod protocol;`
- `automarket-iroh/src/protocol.rs` — create new file

## Verification

- `cargo check -p automarket-iroh` compiles successfully.
