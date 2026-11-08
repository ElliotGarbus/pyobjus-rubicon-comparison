#!/usr/bin/env bash
# Build E3's Objective-C bridge as an xcframework, with manual reference
# counting as kivy-ios's template compiles it. The app links it, so the bridge
# class is loaded at launch, as it is in a kivy-ios app.
# Usage: build_bridge.sh OUT_DIR
set -euo pipefail
OUT=$(cd "$1" && pwd)
SRC=$(cd "$(dirname "$0")/../../../examples/section-04" && pwd)
NAME=S4Bridge
rm -rf "$OUT/$NAME.xcframework" "$OUT/fw-$NAME"
args=()
for sdk in iphoneos iphonesimulator; do
  if [[ $sdk == iphoneos ]]; then target=arm64-apple-ios16.0; plat=iPhoneOS; else target=arm64-apple-ios16.0-simulator; plat=iPhoneSimulator; fi
  fw=$OUT/fw-$NAME/$sdk/$NAME.framework
  mkdir -p "$fw"
  xcrun --sdk $sdk clang -target "$target" -isysroot "$(xcrun --sdk $sdk --show-sdk-path)" -dynamiclib \
    -fno-objc-arc -framework Foundation -framework CoreMotion -I "$SRC" \
    -install_name "@rpath/$NAME.framework/$NAME" "$SRC/e3_bridge.m" -o "$fw/$NAME"
  cat > "$fw/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>$NAME</string>
<key>CFBundleIdentifier</key><string>org.comparison.s4bridge</string>
<key>CFBundleName</key><string>$NAME</string>
<key>CFBundlePackageType</key><string>FMWK</string>
<key>CFBundleShortVersionString</key><string>1.0</string>
<key>CFBundleVersion</key><string>1</string>
<key>CFBundleSupportedPlatforms</key><array><string>$plat</string></array>
<key>MinimumOSVersion</key><string>16.0</string>
</dict></plist>
PLIST
  args+=(-framework "$fw")
done
xcodebuild -create-xcframework "${args[@]}" -output "$OUT/$NAME.xcframework"
