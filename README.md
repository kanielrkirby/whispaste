# whispaste

[![Build](https://github.com/kanielrkirby/whispaste/actions/workflows/build.yml/badge.svg)](https://github.com/kanielrkirby/whispaste/actions/workflows/build.yml)
[![Test](https://github.com/kanielrkirby/whispaste/actions/workflows/test.yml/badge.svg)](https://github.com/kanielrkirby/whispaste/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/whispaste)](https://pypi.org/project/whispaste/)
[![License](https://img.shields.io/github/license/kanielrkirby/whispaste)](LICENSE)

Simple voice-to-text paste tool.

## Install

### Nix (recommended)

```bash
nix build
nix run github:kanielrkirby/whispaste
```

### PyPI

```bash
pip install whispaste
```

### Linux packages

```bash
# Debian/Ubuntu (.deb)
make deb
sudo dpkg -i whispaste_*.deb

# Fedora/RHEL/CentOS (.rpm)
make rpm
sudo rpm -i whispaste-*.rpm

# Alpine Linux (.apk)
make apk
sudo apk add --allow-untrusted whispaste-*.apk

# Arch Linux
make arch
sudo pacman -U whispaste-*.pkg.tar.zst
```

### Build all packages

```bash
make all
```

### Build specific package

```bash
make deb       # or rpm, apk, arch, pip
```

### Snap

```bash
sudo snap install whispaste
```

### Flatpak

```bash
flatpak install flathub com.github.whispaste
```

### AppImage

Download and run the `.AppImage` file from [releases](https://github.com/kanielrkirby/whispaste/releases).

### Homebrew

```bash
brew tap kanielrkirby/whispaste
brew install whispaste
```

## Try Without Installing

```bash
nix run github:kanielrkirby/whispaste
```

## Usage

whispaste is a toggle - run it once to start recording, run it again to stop, transcribe, and paste:

```bash
whispaste          # Start recording
whispaste          # Stop, transcribe, and paste at cursor
```

### Options

```bash
whispaste --clipboard              # Copy to clipboard instead of pasting
whispaste --template translate     # Post-process with built-in template
whispaste --template cleanup       # Clean up transcription (fix grammar, remove fillers)
whispaste --template organize      # Organize into structured document
whispaste --post-prompt "..."      # Custom post-processing prompt
whispaste --post-model gpt-4o      # Use specific model for post-processing
```

### Keybinding Example

Bind to a hotkey for hands-free operation. For example, in Hyprland:

```
bind = , F9, exec, whispaste
bind = SHIFT, F9, exec, whispaste --clipboard
```

Or in i3/sway:

```
bindsym F9 exec whispaste
bindsym Shift+F9 exec whispaste --clipboard
```

Or in dwm (`config.h`):

```c
static const char *whispaste[] = { "whispaste", NULL };
static const char *whispaste_clip[] = { "whispaste", "--clipboard", NULL };

static const Key keys[] = {
    { 0,       XK_F9, spawn, {.v = whispaste } },
    { ShiftMask, XK_F9, spawn, {.v = whispaste_clip } },
};
```

## Setup

Set `OPENAI_API_KEY` in environment or `~/.config/whispaste/.env`:

```bash
echo 'OPENAI_API_KEY=your_key' > ~/.config/whispaste/.env
```

## Platform Support

whispaste is designed to be cross-platform, with platform-specific backends for clipboard, typing, and notifications.

| Platform | Status | Notes |
|----------|--------|-------|
| Linux (Wayland) | Tested | Requires `wl-clipboard`, `wtype` or `ydotool` |
| Linux (X11) | Tested | Requires `xclip` or `xsel`, `xdotool` |
| macOS | CI Tested | Uses `pbcopy` and `osascript` |
| Windows | CI Tested | Uses `clip` and PowerShell |

Note: macOS and Windows are tested in CI (install + import), but haven't been manually tested end-to-end. Please report issues!

### Linux Requirements

- `libnotify` for notifications
- Wayland: `wl-clipboard`, `wtype` or `ydotool`
- X11: `xclip` or `xsel`, `xdotool`

## How It Works

1. First invocation starts a background daemon that records audio
2. Second invocation signals the daemon to stop recording
3. Audio is sent to OpenAI Whisper API for transcription
4. Text is inserted at cursor (via primary selection + paste, or typing fallback)
5. Falls back to clipboard if insertion fails

## License

MIT
