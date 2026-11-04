#!/usr/bin/env bash
# Build the iOS wheels the Section 2 apps use, at the baseline's pinned commits.
#
# pyobjus publishes no iOS wheels. kivy-mobile-wheels' recipe needs the CPython
# 3.15 macOS framework installed by hand and builds a different pin, so this
# compiles the same sources, flags and libffi directly.
#
# pyobjus's .ci/build_ios_dependencies.sh stops on Xcode 27, which refuses the
# libffi project's iOS 8.0 target. It's run once to generate the sources, then
# xcodebuild is rerun with a 16.0 target. No source is changed.
#
# Usage: build_wheels.sh WORK PYOBJUS_REPO RUBICON_REPO
set -euo pipefail

WORK=$(cd "$1" && pwd)
PYOBJUS_REPO=$(cd "$2" && pwd)
RUBICON_REPO=$(cd "$3" && pwd)
PYOBJUS_PINS="release=v1.2.4 main=0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81"
RUBICON_MAIN=6bf06390f720226da3d51477f38de3ff1e680eaf
PY_URL=https://www.python.org/ftp/python/3.15.0/python-3.15.0-iOS-XCframework.tar.gz
PY_SHA=68e98ab35cc0643ba3a227a8c7768da45c2a5e67dbe1bc26598537e96680fd19
HERE=$(cd "$(dirname "$0")" && pwd)
IOS=16.0

# --- Python.xcframework: headers and the framework extensions link against ----
PY=$WORK/python/Python.xcframework
if [[ ! -d $PY ]]; then
  mkdir -p "$WORK/python"
  curl -fsSL -o "$WORK/python/py.tgz" "$PY_URL"
  echo "$PY_SHA  $WORK/python/py.tgz" | shasum -a 256 -c -
  tar -xzf "$WORK/python/py.tgz" -C "$WORK/python"
fi

# --- libffi -------------------------------------------------------------------
DEPS=$WORK/deps
FFI_SRC=$DEPS/ios-deps-build/libffi-3.5.2
mkdir -p "$DEPS"
if [[ ! -d $FFI_SRC/build_iphoneos-arm64 ]]; then
  (cd "$DEPS" && bash "$PYOBJUS_REPO/.ci/build_ios_dependencies.sh" > build.log 2>&1) || true
fi
for sdk in iphoneos iphonesimulator; do
  dest=$DEPS/ios-deps-install/$sdk/arm64
  if [[ ! -f $dest/lib/libffi.a ]]; then
    (cd "$FFI_SRC" && xcodebuild ONLY_ACTIVE_ARCH=NO ARCHS=arm64 IPHONEOS_DEPLOYMENT_TARGET=$IOS \
       -sdk $sdk -project libffi.xcodeproj -target libffi-iOS -configuration Release > "$DEPS/$sdk.log" 2>&1)
    mkdir -p "$dest/lib"
    cp "$FFI_SRC/build/Release-$sdk/libffi.a" "$dest/lib/"
    cp -R "$FFI_SRC/build/Release-$sdk/include" "$dest/include"
  fi
done

# --- pyobjus ------------------------------------------------------------------
build_pyobjus() {
  local label=$1 ref=$2
  local src=$WORK/src/pyobjus-$label out=$WORK/wheels/$label
  rm -rf "$src"; mkdir -p "$src" "$out"
  git -C "$PYOBJUS_REPO" archive "$ref" pyobjus LICENSE | tar -x -C "$src"
  printf 'DEF PLATFORM = "ios"\nDEF ARCH = "arm64"\n' > "$src/pyobjus/config.pxi"
  uvx --from 'cython==3.3.1' --python 3.14 cython -I "$src/pyobjus" \
    -o "$src/pyobjus/pyobjus.c" "$src/pyobjus/pyobjus.pyx" 2>&1 | tail -1
  local sdk slice target version
  version=$(sed -n "s/^__version__ = '\(.*\)'/\1/p" "$src/pyobjus/__init__.py")
  for sdk in iphoneos iphonesimulator; do
    if [[ $sdk == iphoneos ]]; then slice=ios-arm64; target=arm64-apple-ios$IOS
    else slice=ios-arm64_x86_64-simulator; target=arm64-apple-ios$IOS-simulator; fi
    local ffi=$DEPS/ios-deps-install/$sdk/arm64
    local so=$src/pyobjus/pyobjus.cpython-315-$sdk.so
    local cc=(xcrun --sdk $sdk clang -target "$target" -isysroot "$(xcrun --sdk $sdk --show-sdk-path)")
    "${cc[@]}" -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer -fno-strict-overflow -fno-common \
      -dynamic -DNDEBUG -g -O3 -w -I"$PY/$slice/include/python3.15" -I"$ffi/include" -I"$ffi/include/ffi" \
      -I"$src/pyobjus" -c "$src/pyobjus/pyobjus.c" -o "$src/pyobjus-$sdk.o"
    "${cc[@]}" -dynamiclib -F "$PY/$slice" -framework Python -framework CoreFoundation \
      -L"$ffi/lib" -lffi -lobjc "$src/pyobjus-$sdk.o" -o "$so"
    python3 "$HERE/pack_wheel.py" "$src" "$version" "$sdk" "$out"
    rm "$so"
  done
}
for pin in $PYOBJUS_PINS; do build_pyobjus "${pin%%=*}" "${pin#*=}"; done

# --- Rubicon: 0.5.7 comes from PyPI; the default branch is built here ----------
mkdir -p "$WORK/wheels/main"
# No local version segment: KivyForge's install step rejects a percent-encoded "+".
SETUPTOOLS_SCM_PRETEND_VERSION=0.5.8.dev21 \
  uv build --wheel --python 3.14 --out-dir "$WORK/wheels/main" "$RUBICON_REPO"
git -C "$RUBICON_REPO" rev-parse HEAD | grep -qx "$RUBICON_MAIN"

ls -l "$WORK"/wheels/*
