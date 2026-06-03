---
stage: draft_review
depends_on:
  - 0003_postcard_serde_for_automarket_iroh-subtask-01-add-deps-and-enum
  - 0003_postcard_serde_for_automarket_iroh-subtask-02-refactor-ping
  - 0003_postcard_serde_for_automarket_iroh-subtask-03-update-docs
---

# Title: Use postcard serde for automarket-iroh protocol messages

## Description

Replace raw byte-string matching in `automarket-iroh` protocols with structured serde encoding/decoding using `postcard`. postcard is the de facto serde format for iroh — it is compact, zero-copy friendly, `#[no_std]`-compatible, and already used by iroh internally for its own wire format.

Currently `automarket-iroh::ping` sends and matches on raw `b"ping"` / `b"pong"` byte slices. As we add more protocols (data queries, trading signals, etc.), raw byte matching does not scale — there is no type safety, no schema evolution, no way to encode structured payloads (numbers, enums, nested structs), and message boundaries must be handled manually.

## Changes Required (Summary)

### 1. Add `postcard` + `serde` dependencies

Add to `automarket-iroh/Cargo.toml`:
```toml
serde = { version = "1", features = ["derive"] }
postcard = { version = "1", default-features = false }
```

### 2. Create `protocol.rs` with `PingMessage` enum

New file `automarket-iroh/src/protocol.rs`:
```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PingMessage {
    Ping,
    Pong,
    Unknown,
}
```

Register in `automarket-iroh/src/lib.rs`:
```rust
pub mod ping;
pub mod protocol;
```

### 3. Refactor `ping.rs` to use postcard encoding

- **Import**: `use crate::protocol::PingMessage;`
- **`handle_connection` (server, line 40)**: Replace raw byte match with `postcard::from_bytes(&msg).unwrap_or(PingMessage::Unknown)`, then serialize the response via `postcard::to_vec(...)`.
- **`ping` function (client, line 82)**: Replace `b"ping"` with `postcard::to_vec(&PingMessage::Ping)`.
- **Response check (line 88-91)**: Deserialize `response` via `postcard::from_bytes(...)` and compare to `PingMessage::Pong`.
- **`PingError::UnexpectedResponse`**: Change `got: Vec<u8>` to `got: PingMessage`.
- **Add `PingError::Decode(String)`** variant for postcard deserialization errors.
- **Tests**: Update `test_ping_unexpected_response` to send/receive postcard-encoded messages.

### 4. Consumers

- `automarket-runner/src/iroh_server.rs` — no code change needed (uses `PingProtocol` struct which delegates to `handle_connection`).
- `automarket-runner/examples/ping_client.rs` — no change needed (uses `ping::ping()` convenience function).
- `automarket-browser/src/main.rs` — no change needed.

### 5. Keep ALPN unchanged

The ALPN stays `b"automarket/ping/0"` — the wire format change is compatible as long as both sides are updated together. No protocol version bump needed for a single crate cycle.

## Error Handling Strategy

| Scenario | Server (`handle_connection`) | Client (`ping`) |
|---|---|---|
| Garbage bytes from peer | `postcard::from_bytes(...).unwrap_or(PingMessage::Unknown)` → responds with `Unknown` | `postcard::from_bytes(...).map_err(PingError::Decode)` → propagates as error |
| Valid postcard, wrong variant | `PingMessage::Unknown` → responds with `Unknown` | Compares against `PingMessage::Pong`, returns `PingError::UnexpectedResponse { got: ... }` |

## Verification

- `cargo test -p automarket-iroh` passes.
- `cargo test --workspace` passes.
- Example client (`cargo run --example ping_client`) works end-to-end.
- `cargo fmt` leaves no changes.

## Sub-Tasks

The work is split into three sequential sub-tasks:

| # | Sub-ticket | Description |
|---|---|---|
| 1 | `0003_postcard_serde_for_automarket_iroh-subtask-01-add-deps-and-enum` | Add `serde` + `postcard` deps, create `protocol.rs` with `PingMessage` enum, register module |
| 2 | `0003_postcard_serde_for_automarket_iroh-subtask-02-refactor-ping` | Rewrite `ping.rs` to use postcard — encoding, decoding, error types, tests |
| 3 | `0003_postcard_serde_for_automarket_iroh-subtask-03-update-docs` | Update `docs/automarket-iroh.md` and `CHANGELOG.md` |

Execute in order (each depends on the prior).

## Future Protocols

Once postcard serde is established, new protocols (e.g. `automarket/data/0`, `automarket/signal/0`) can define their own `Serialize + Deserialize` message enums and reuse the same encoding pattern. Consider extracting common send/recv helpers into a shared module (e.g. a `pub fn send_msg<T: Serialize>` / `pub fn recv_msg<T: Deserialize>` in `protocol.rs`).

## Conversation

### Admin refinement (2026-06-03)

The original draft ticket had several issues corrected during refinement:

1. **Fixed incorrect paths**: All references to `crates/automarket-iroh/...` were changed to `automarket-iroh/...` (flat repo layout, no `crates/` prefix).

2. **Made module placement definitive**: The draft said "Add a new file (e.g. `src/protocol.rs`) or fold into `ping.rs`" — refined to create `protocol.rs` definitively, since the "Future Protocols" section already envisions shared helpers that belong in a separate module.

3. **Added `lib.rs` registration step**: The draft omitted registering `pub mod protocol;` in `lib.rs` — added as a required step.

4. **Expanded `PingError`**: Added a `Decode(String)` variant for postcard deserialization errors. The original draft didn't address how decode failures propagate.

5. **Specified error handling strategy**: Documented the server-side `unwrap_or(PingMessage::Unknown)` approach vs client-side `map_err(PingError::Decode)`.

6. **Added `PartialEq` + `Eq` derives**: Required so `PingMessage::Ping == PingMessage::Ping` comparisons compile in both the handler and tests.

7. **Updated test details**: The `test_ping_unexpected_response` test sends `PingMessage::Unknown` and asserts on `PingMessage::Unknown` rather than raw bytes.

8. **Split into 3 sub-tasks**: Implemented as separate sub-tickets so work can be parallelized and tracked independently.

9. **Added error handling table**: Quick-reference for developer to see server vs client error behavior at a glance.
