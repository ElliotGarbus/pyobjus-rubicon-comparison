#!/usr/bin/env bash
# Build the fixture and the F1.6 library as xcframeworks, from the same
# sources the Mac uses. The Swift library is built by KivyForge as a local
# package instead (see make_project.py).
# Usage: build_frameworks.sh OUT_DIR
set -euo pipefail
OUT=$(cd "$1" && pwd)
SRC=$(cd "$(dirname "$0")/.." && pwd)

build() {  # name source frameworks...
  local name=$1 src=$2; shift 2
  rm -rf "$OUT/$name.xcframework" "$OUT/fw-$name"
  local args=()
  for sdk in iphoneos iphonesimulator; do
    if [[ $sdk == iphoneos ]]; then target=arm64-apple-ios16.0; plat=iPhoneOS; else target=arm64-apple-ios16.0-simulator; plat=iPhoneSimulator; fi
    local fw=$OUT/fw-$name/$sdk/$name.framework
    mkdir -p "$fw"
    local links=()
    for f in "$@"; do links+=(-framework "$f"); done
    xcrun --sdk $sdk clang -target "$target" -isysroot "$(xcrun --sdk $sdk --show-sdk-path)" -dynamiclib \
      -fobjc-arc "${links[@]}" -Wall -install_name "@rpath/$name.framework/$name" "$src" -o "$fw/$name"
    cat > "$fw/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>$name</string>
<key>CFBundleIdentifier</key><string>org.comparison.$(echo $name | tr 'A-Z' 'a-z')</string>
<key>CFBundleName</key><string>$name</string>
<key>CFBundlePackageType</key><string>FMWK</string>
<key>CFBundleShortVersionString</key><string>1.0</string>
<key>CFBundleVersion</key><string>1</string>
<key>CFBundleSupportedPlatforms</key><array><string>$plat</string></array>
<key>MinimumOSVersion</key><string>16.0</string>
</dict></plist>
PLIST
    args+=(-framework "$fw")
  done
  xcodebuild -create-xcframework "${args[@]}" -output "$OUT/$name.xcframework"
}

build S3Fixture "$SRC/s3fixture.m" Foundation CoreGraphics
build S3Extra "$SRC/s3extra.m" Foundation
