# whispaste

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

```bash
whispaste  # Start recording
whispaste  # Stop, transcribe, and paste at cursor
```

## Setup

Set `OPENAI_API_KEY` in environment or `~/.config/whispaste/.env`:

```bash
echo 'OPENAI_API_KEY=your_key' > .env
```

## Requirements

- Linux:
  - `libnotify` for notifications
  - Wayland
    - `wl-clipboard`
    - `wtype` or `ydotool`
  - X11
    - `xclip` or `xsel`
    - `xdotool`
- macOS: Built-in support
- Windows: Built-in support
