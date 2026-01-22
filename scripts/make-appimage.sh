#!/bin/bash
set -e

BIN_PATH=$(nix-build --print-build-logs)
VERSION="0.1.0"
APPDIR="whispaste-$VERSION.AppDir"
OUTPUT="whispaste-$VERSION-x86_64.AppImage"

echo "Building AppImage for whispaste..."

rm -rf "$APPDIR" "$OUTPUT"
mkdir -p "$APPDIR"

mkdir -p "$APPDIR/usr/bin"
cp "$BIN_PATH/bin/whispaste" "$APPDIR/usr/bin/whispaste"
chmod +x "$APPDIR/usr/bin/whispaste"

mkdir -p "$APPDIR/usr/share/applications"
cat > "$APPDIR/usr/share/applications/com.github.whispaste.desktop" <<'EOF'
[Desktop Entry]
Name=whispaste
Comment=Voice-to-paste tool using OpenAI Whisper
Exec=whispaste
Icon=com.github.whispaste
Type=Application
Terminal=true
Categories=Audio;Utility;
Keywords=audio;speech;transcription;whisper;
EOF

mkdir -p "$APPDIR/usr/share/metainfo"
cat > "$APPDIR/usr/share/metainfo/com.github.whispaste.metainfo.xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.github.whispaste</id>
  <name>whispaste</name>
  <summary>Simple voice-to-paste tool using OpenAI Whisper</summary>
  <description>
    <p>Record audio with a hotkey and paste transcription at cursor using OpenAI's Whisper API.</p>
  </description>
  <url type="homepage">https://github.com/kanielrkirby/whispaste</url>
  <url type="bugtracker">https://github.com/kanielrkirby/whispaste/issues</url>
  <metadata_license>MIT</metadata_license>
  <project_license>MIT</project_license>
  <developer_name>whispaste contributors</developer_name>
  <content_rating type="oars-1.1" />
  <releases>
    <release version="0.1.0" date="2025-01-22" />
  </releases>
</component>
EOF

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=$(dirname "$SELF")

export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/whispaste" "$@"
EOF
chmod +x "$APPDIR/AppRun"

ARCHIVE_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
echo "Downloading appimagetool..."
curl -L -o appimagetool "$ARCHIVE_URL"
chmod +x appimagetool

echo "Creating AppImage..."
./appimagetool "$APPDIR" "$OUTPUT"

rm -rf "$APPDIR" appimagetool

echo "AppImage created: $OUTPUT"
