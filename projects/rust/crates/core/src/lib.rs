//! A "widely depended" core crate (spec §4.1) — the leaf crate below depends on it, so a change
//! here would be the "core" change-kind, while a change in crates/leaf is the "leaf" change-kind
//! that nothing else depends on. Uses serde/serde_json (proc-macro derive) so there's a real,
//! non-trivial compile unit worth caching.
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, PartialEq)]
pub struct Greeting {
    pub message: String,
}

pub fn greeting_json() -> String {
    serde_json::to_string(&Greeting { message: "hello from showcase-core".to_string() })
        .expect("serialization cannot fail for this fixed struct")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn greeting_json_is_valid() {
        assert!(greeting_json().contains("hello from showcase-core"));
    }
}
