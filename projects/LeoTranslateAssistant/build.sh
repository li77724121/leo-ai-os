#!/bin/bash
# build.sh — 编译 Leo Translate Assistant v1.0
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="LeoTranslateAssistant"
BUNDLE_ID="com.leo.translate.assistant"
SRC_DIR="$PROJECT_DIR/$APP_NAME"
BUILD_DIR="$PROJECT_DIR/build"
APP_BUNDLE="$BUILD_DIR/$APP_NAME.app"
CONTENTS="$APP_BUNDLE/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

echo "=== 编译 Leo Translate Assistant v1.0 ==="

# 1. 清理
rm -rf "$BUILD_DIR"
mkdir -p "$MACOS" "$RESOURCES"

# 2. 编译所有 Swift 文件
echo "编译 Swift 源文件..."
cd "$SRC_DIR"
swiftc \
    -o "$MACOS/$APP_NAME" \
    -emit-executable \
    -module-name "$APP_NAME" \
    -target arm64-apple-macos14.0 \
    -sdk "$(xcrun --show-sdk-path --sdk macosx)" \
    -framework SwiftUI \
    -framework AppKit \
    -framework Foundation \
    -framework UserNotifications \
    -I "$(xcrun --show-sdk-path --sdk macosx)/System/Library/Frameworks/SwiftUI.framework" \
    -parse-as-library \
    -O \
    -whole-module-optimization \
    *.swift 2>&1

echo "✅ 编译完成"

# 3. 复制 Info.plist
cp "$SRC_DIR/Info.plist" "$CONTENTS/"
plutil -replace CFBundleExecutable -string "$APP_NAME" "$CONTENTS/Info.plist"
plutil -replace CFBundleIdentifier -string "$BUNDLE_ID" "$CONTENTS/Info.plist"
echo "✅ Info.plist 已配置"

# 4. 注册 Services（右键菜单）
mkdir -p "$HOME/Library/Services"
cat > "$HOME/Library/Services/Leo翻译.workflow/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSServices</key>
    <array>
        <dict>
            <key>NSMenuItem</key>
            <dict>
                <key>default</key>
                <string>翻译中文</string>
            </dict>
            <key>NSMessage</key>
            <string>runService</string>
            <key>NSSendTypes</key>
            <array>
                <string>NSStringPboardType</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
PLIST
echo "✅ Services 已注册"

# 5. 代码签名
codesign --force --deep --sign - "$APP_BUNDLE" 2>/dev/null || true
echo "✅ 签名完成"

# 6. 创建 .dmg
echo "创建 DMG..."
DMG_PATH="$BUILD_DIR/$APP_NAME-v1.0.dmg"
hdiutil create -volname "$APP_NAME" -srcfolder "$APP_BUNDLE" -ov -format UDZO "$DMG_PATH" 2>/dev/null
echo "✅ DMG: $DMG_PATH"

echo ""
echo "========================"
echo "🎉 构建完成!"
echo "📦 App: $APP_BUNDLE"
echo "📀 DMG: $DMG_PATH"
echo "========================"
echo ""
echo "🔍 在 Finder 中打开:"
echo "open $BUILD_DIR"
