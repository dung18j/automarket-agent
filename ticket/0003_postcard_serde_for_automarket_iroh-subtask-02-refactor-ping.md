---
stage: todo
parent: 0003_postcard_serde_for_automarket_iroh
dependencies:
  - 0003_postcard_serde_for_automarket_iroh-subtask-01-add-deps-and-enum
---

# Subtask: Refactor ping.rs to use postcard-encoded PingMessage

## Description

Replace all raw byte-string matching in `automarket-iroh/src/ping.rs` with postcard-encoded `PingMessage` variants from the new `protocol` module.

## Changes Required

### 1. Add import

At the top of `ping.rs`:
```rust
use crate::protocol::PingMessage;
```

### 2. Update `handle_connection` (server side)

Replace line 40:
```rust
let response: &[u8] = if msg == b"ping" { b"pong" } else { b"unknown" };
```
with:
```rust
let request: PingMessage = postcard::from_bytes(&msg).unwrap_or(PingMessage::Unknown);
let response: PingMessage = if request == PingMessage::Ping {
    PingMessage::Pong
} else {
    PingMessage::Unknown
};
let encoded = postcard::to_vec(&response).expect("infallible serialization");
```

Then replace `send.write_all(response)` with `send.write_all(&encoded)`.

### 3. Update `ping` function (client side)

Replace line 82:
```rust
send.write_all(b"ping").await?;
```
with:
```rust
let encoded = postcard::to_vec(&PingMessage::Ping).expect("infallible serialization");
send.write_all(&encoded).await?;
```

Replace lines 88-91:
```rust
if response == b"pong" {
    Ok(elapsed)
} else {
    Err(PingError::UnexpectedResponse { got: response })
}
```
with:
```rust
let pong: PingMessage = postcard::from_bytes(&response)
    .map_err(|e| PingError::Decode(e.to_string()))?;
if pong == PingMessage::Pong {
    Ok(elapsed)
} else {
    Err(PingError::UnexpectedResponse { got: pong })
}
```

### 4. Update `PingError` enum

Replace the `UnexpectedResponse` variant:
```rust
/// Received an unexpected response payload.
#[error("unexpected response (got {got:?}, expected pong)")]
UnexpectedResponse { got: PingMessage },
```

Add a `Decode` variant for postcard deserialization errors:
```rust
/// Failed to decode protocol message.
#[error("decode error: {0}")]
Decode(String),
```

### 5. Update tests

In `test_ping_unexpected_response`:

Replace line 131:
```rust
send.write_all(b"not-ping").await.unwrap();
```
with:
```rust
let bogus = postcard::to_vec(&PingMessage::Unknown).expect("infallible");
send.write_all(&bogus).await.unwrap();
```

Replace lines 135-136:
```rust
// Server responds with b"unknown" for unrecognized messages.
assert_eq!(response, b"unknown");
```
with:
```rust
let decoded: PingMessage = postcard::from_bytes(&response).unwrap();
assert_eq!(decoded, PingMessage::Unknown);
```

No changes needed in `test_ping_pong` — it uses the `ping()` convenience function which is transparent to existing assertions.

## Error Handling Notes

- Server uses `unwrap_or(PingMessage::Unknown)` for decoding failures — if the peer sends garbage, the server still responds with `Unknown` gracefully.
- Client uses `map_err` on decode failure, converting to `PingError::Decode(String)` — preserves the existing error-handling pattern.
- `postcard::to_vec()` panics on `expect(...)` but this enum has no data fields, so serialization is truly infallible.

## Files to Modify

- `automarket-iroh/src/ping.rs` — all changes listed above

## Verification

- `cargo test -p automarket-iroh` passes.
- Both `test_ping_pong` and `test_ping_unexpected_response` pass.
