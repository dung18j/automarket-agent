---
stage: draft_refining
claimed_from: draft
claimed_at: 2026-06-03T09:43:04Z
depends_on: []
---

# Title: Use postcard serde for automarket-iroh protocol messages

## Description

Replace raw byte-string matching in `automarket-iroh` protocols with structured serde encoding/decoding using `postcard`. postcard is the de facto serde format for iroh — it is compact, zero-copy friendly, `#[no_std]`-compatible, and already used by iroh internally for its own wire format.

Currently `automarket-iroh::ping` sends and matches on raw `b"ping"` / `b"pong"` byte slices. As we add more protocols (data queries, trading signals, etc.), raw byte matching does not scale — there is no type safety, no schema evolution, no way to encode structured payloads (numbers, enums, nested structs), and message boundaries must be handled manually.

## Changes Required

### 1. Add `postcard` + `serde` dependencies

Add to `crates/automarket-iroh/Cargo.toml`:
```toml
serde = { version = "1", features = ["derive"] }
postcard = { version = "1", default-features = false }
```

### 2. Define a shared message enum

Add a new file (e.g. `src/protocol.rs`) or fold into `ping.rs`:

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub enum PingMessage {
    Ping,
    Pong,
    Unknown,
}
```

### 3. Update `ping.rs`

- Replace `b"ping"` / `b"pong"` / `b"unknown"` with postcard-encoded `PingMessage` variants.
- Use `postcard::to_vec()` on send and `postcard::from_bytes()` on receive.
- Update `PingError::UnexpectedResponse` to carry a `PingMessage` instead of raw bytes.

### 4. Update consumers

- `automarket-runner/src/iroh_server.rs` — no code change needed (it uses `PingProtocol` struct which delegates to `handle_connection`).
- `automarket-runner/examples/ping_client.rs` — no change (uses `ping::ping()` function).
- `automarket-browser/src/main.rs` — no change.

### 5. Keep ALPN unchanged

The ALPN stays `b"automarket/ping/0"` — the wire format change is compatible as long as both sides are updated together. No protocol version bump needed for a single crate cycle.

## Verification

- `cargo test -p automarket-iroh` passes.
- `cargo test --workspace` passes.
- Existing integration tests (`test_ping_pong`, `test_ping_unexpected_response`) are updated to use the new enum-based messages.
- Example client still works end-to-end.

## Future Protocols

Once postcard serde is established, new protocols (e.g. `automarket/data/0`, `automarket/signal/0`) can define their own `Serialize + Deserialize` message enums and reuse the same encoding pattern. Consider extracting common send/recv helpers into a shared module.

## Conversation

