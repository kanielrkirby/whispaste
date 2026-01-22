.PHONY: help build deb rpm apk arch pip clean

help:
	@echo "Package whispaste for multiple platforms"
	@echo ""
	@echo "Targets:"
	@echo "  build     - Build Nix package"
	@echo "  pip       - Build PyPI wheel/sdist"
	@echo "  deb       - Build Debian .deb package"
	@echo "  rpm       - Build RedHat .rpm package"
	@echo "  apk       - Build Alpine .apk package"
	@echo "  arch      - Build Arch Linux package"
	@echo "  all       - Build all nfpm packages"
	@echo "  clean     - Remove build artifacts"
	@echo ""
	@echo "CI/CD builds (require additional tools):"
	@echo "  snap      - Snap package"
	@echo "  flatpak   - Flatpak bundle"
	@echo "  appimage  - AppImage bundle"

build:
	nix build

pip:
	python -m build

deb:
	nix build
	nfpm package -p deb

rpm:
	nix build
	nfpm package -p rpm

apk:
	nix build
	nfpm package -p apk

arch:
	nix build
	nfpm package -p archlinux

all: deb rpm apk arch pip

clean:
	rm -rf dist result *.deb *.rpm *.apk *.pkg.tar.zst

# CI/CD builds - require nix-bundle, flatpak-builder, snapcraft

snap:
	snapcraft

flatpak:
	flatpak-builder --user build flatpak/com.github.whispaste.yml

appimage:
	nix2appimage.sh $(nix build)
