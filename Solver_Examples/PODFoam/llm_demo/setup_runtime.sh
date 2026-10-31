#!/usr/bin/env bash
# Download the pinned model, image projector and llama.cpp server binary into
# POD_LLM_RUNTIME (default: ../llm-runtime next to the PythonFOAM checkout),
# check their SHA-256 and write the runtime manifest. About 3.4 GB in total.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
runtime_dir="${POD_LLM_RUNTIME:-$script_dir/../../../../llm-runtime}"
mkdir -p -- "$runtime_dir"
cd -- "$runtime_dir"
runtime_dir=$(pwd)

revision=b4243c156154b6dca9324415f8c7ccc098b4aed1
model=gemma-4-E2B-it-Q4_0.gguf
projector=mmproj-gemma-4-E2B-it-Q8_0.gguf
archive=llama-b11429-bin-ubuntu-x64.tar.gz

fetch() {
    local url=$1 target=$2
    if [[ ! -f "$target" ]]; then
        curl --fail --location --retry 3 --continue-at - "$url" --output "$target.partial"
        mv -- "$target.partial" "$target"
    fi
}
fetch "https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF/resolve/$revision/$model" "$model"
fetch "https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF/resolve/$revision/$projector" "$projector"
fetch "https://github.com/ggml-org/llama.cpp/releases/download/b11429/$archive" "$archive"

printf '%s\n' \
    "8e30dff3ac4c8434c49a7036fa15564bdbb6044e42bf04550bf1a096ad7e6a52  $model" \
    "9406f99c16d68cda4f1f0552192dcc99021ea1fc6d2fd50b1dc3ccf30d04b292  $projector" \
    "f6d25dde8f51133143d1453da4fd5f73b145127177612a283bf7995957af3392  $archive" | sha256sum --check
if [[ ! -x llama-b11429/llama-server ]]; then
    tar -xzf "$archive"
fi
POD_LLM_RUNTIME="$runtime_dir" "${PYTHON:-python3}" "$script_dir/runtime.py" verify
