#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
# SPDX-License-Identifier: GPL-3.0-only

set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_root="$(mktemp -d "${TMPDIR:-/tmp}/douyi-rapfi.XXXXXX")"
rapfi_dir="$build_root/rapfi-source"

cleanup() {
  rm -rf -- "$build_root"
}
trap cleanup EXIT

git clone --depth 1 --branch 250615 --recurse-submodules --shallow-submodules \
  https://github.com/dhbloo/rapfi.git "$rapfi_dir"
git -C "$rapfi_dir" apply "$root_dir/patches/rapfi-wasm-single-thread.patch"

cp "$root_dir/engine/config.toml" "$rapfi_dir/Networks/config.toml"
cp "$root_dir/engine/model210901.bin" "$rapfi_dir/Networks/model210901.bin"
cp "$root_dir/engine/mix9svqfreestyle_bsmix.bin.lz4" "$rapfi_dir/Networks/mix9svqfreestyle_bsmix.bin.lz4"
printf '%s\n' \
  'config.toml@config.toml' \
  'model210901.bin@model210901.bin' \
  'mix9svqfreestyle_bsmix.bin.lz4@mix9svqfreestyle_bsmix.bin.lz4' \
  > "$rapfi_dir/Networks/wasm_preloads.txt"

cmake -E make_directory "$rapfi_dir/Rapfi/build-wasm"
pushd "$rapfi_dir/Rapfi/build-wasm" >/dev/null
emcmake cmake .. -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DNO_MULTI_THREADING=ON \
  -DNO_COMMAND_MODULES=ON \
  -DUSE_SSE=OFF \
  -DUSE_AVX2=OFF \
  -DUSE_AVX512=OFF \
  -DUSE_BMI2=OFF \
  -DUSE_VNNI=OFF \
  -DUSE_NEON=OFF \
  -DUSE_NEON_DOTPROD=OFF \
  -DUSE_WASM_SIMD=ON \
  -DUSE_WASM_SIMD_RELAXED=OFF
cmake --build . --parallel 2
popd >/dev/null

for destination in \
  "$root_dir/android/app/src/main/assets/engine" \
  "$root_dir/ios/DouYi/Web/engine"
do
  mkdir -p "$destination"
  cp "$rapfi_dir/Rapfi/build-wasm/rapfi-single-simd128.js" "$destination/"
  cp "$rapfi_dir/Rapfi/build-wasm/rapfi-single-simd128.wasm" "$destination/"
  cp "$rapfi_dir/Rapfi/build-wasm/rapfi-single-simd128.data" "$destination/rapfi.data"
done
