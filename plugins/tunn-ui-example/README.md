# Пример интерфейса (Rust)

Исходники: `native/ui-example/`. Библиотека собирается под Android скриптом `tools/build_ui_android.sh` (нужны Rust, `cargo-ndk` и Android NDK) и копируется сюда как `libfq_ui_example.so`; после этого `python3 tools/build.py` собирает архив в `dist/`.
Подробности формата: `docs/UI_ABI.md`.
