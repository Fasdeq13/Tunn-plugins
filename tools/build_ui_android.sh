#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../native/ui-example"
rustup target add aarch64-linux-android
cargo ndk -t arm64-v8a build --release
cp target/aarch64-linux-android/release/libfq_ui_example.so ../../plugins/tunn-ui-example/
cd ../..
python3 tools/build.py
