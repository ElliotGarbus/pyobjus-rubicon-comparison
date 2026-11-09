#!/usr/bin/env bash
# Build the Section 6 fixture as an xcframework, from the source the Mac uses.
# Usage: build_fixture.sh OUT_DIR
set -euo pipefail
OUT=$(cd "$1" && pwd)
SRC=$(cd "$(dirname "$0")/.." && pwd)/s6fixture.m
rm -rf "$OUT/S6Fixture.xcframework" "$OUT/fw"
args=()
for sdk in iphoneos iphonesimulator; do
  if [[ $sdk == iphoneos ]]; then target=arm64-apple-ios16.0; plat=iPhoneOS; else target=arm64-apple-ios16.0-simulator; plat=iPhoneSimulator; fi
  fw=$OUT/fw/$sdk/S6Fixture.framework
  mkdir -p "$fw"
  xcrun --sdk $sdk clang -target "$target" -isysroot "$(xcrun --sdk $sdk --show-sdk-path)" -dynamiclib \
    -O2 -fno-objc-arc -framework Foundation -framework CoreGraphics -framework UIKit -Wall \
    -install_name @rpath/S6Fixture.framework/S6Fixture "$SRC" -o "$fw/S6Fixture"
  cat > "$fw/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>S6Fixture</string>
<key>CFBundleIdentifier</key><string>org.comparison.s6fixture</string>
<key>CFBundleName</key><string>S6Fixture</string>
<key>CFBundlePackageType</key><string>FMWK</string>
<key>CFBundleShortVersionString</key><string>1.0</string>
<key>CFBundleVersion</key><string>1</string>
<key>CFBundleSupportedPlatforms</key><array><string>$plat</string></array>
<key>MinimumOSVersion</key><string>16.0</string>
</dict></plist>
PLIST
  args+=(-framework "$fw")
done
xcodebuild -create-xcframework "${args[@]}" -output "$OUT/S6Fixture.xcframework"
