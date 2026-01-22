# whispaste

Simple voice-to-paste tool.

## Install

```bash
nix build
nix run
```

## Usage

```bash
whispaste  # Start recording (runs in foreground, press Ctrl+C or run again to stop)
whispaste  # Stop, transcribe, and paste at cursor
```

## Setup

Set `OPENAI_API_KEY` in environment or `.env`:

```bash
echo 'OPENAI_API_KEY=your_key' > .env
```

## Requirements

- Linux: `wl-clipboard` (Wayland) or `xdotool` (X11), `libnotify` for notifications
- macOS: Built-in support
- Windows: Built-in support
