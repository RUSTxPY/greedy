# Greedy Native - Rust Shared Library

Fast text normalization for Greedy [DDGS] using Rust.

## Structure

```
src/
├── lib.rs       # Main exports (C ABI)
├── normalize.rs # Text normalization logic
├── utils.rs     # Helper utilities
└── ffi.rs       # FFI helpers
```

## Building

```bash
# Build for current platform
python3 build.py

# Or use cargo directly
cargo build --release
```

## Testing

```bash
# Rust unit tests
cargo test

# Python integration
pytest tests/test_native_text.py -v
```

## Performance

Expected 20-50x speedup over pure Python for text normalization.
