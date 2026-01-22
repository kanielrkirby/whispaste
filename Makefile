.PHONY: help build deb rpm apk archlinux pip clean snap flatpak appimage

help:
	@echo "Package whispaste for multiple platforms"
	@echo ""
	@echo "Targets:"
	@echo "  build      - Build Nix package"
	@echo "  pip        - Build PyPI wheel/sdist"
	@echo "  deb        - Build Debian .deb package"
	@echo "  rpm        - Build RedHat .rpm package"
	@echo "  apk        - Build Alpine .apk package"
	@echo "  archlinux  - Build Arch Linux package"
	@echo "  all        - Build all nfpm packages"
	@echo "  clean      - Remove build artifacts"
	@echo ""
	@echo "CI/CD builds (run in dev shell):"
	@echo "  snap       - Snap package"
	@echo "  flatpak    - Flatpak bundle"
	@echo "  appimage    - AppImage bundle"

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

archlinux:
	nix build
	nfpm package -p archlinux

all: deb rpm apk archlinux pip

clean:
	rm -rf dist result *.deb *.rpm *.apk *.pkg.tar.zst *.snap *.flatpak *.AppImage

snap:
	@echo "Run 'snapcraft' manually after installing snapcraft"
	snapcraft

flatpak:
	@echo "Run 'flatpak-builder' manually after installing flatpak-builder"
	flatpak-builder --user build flatpak/com.github.whispaste.yml

appimage:
	@echo "Run 'nix2appimage.sh' manually after installing nix-bundle"
	nix-build
