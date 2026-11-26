// Depends on showcase-core but nothing depends on leaf — tools/simulate-change.sh edits the
// label() return value here for the "leaf" change kind (spec §4.1 default).
fn label() -> &'static str {
    "leaf-v1"
}

fn main() {
    println!("{}", showcase_core::greeting_json());
    println!("{}", label());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn label_is_not_empty() {
        assert!(!label().is_empty());
    }
}
