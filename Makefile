.PHONY: help build deb rpm apk archlinux pip snap flatpak appimage everything clean test test-deb test-rpm test-apk test-archlinux test-pip

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
	@echo "  snap       - Build Snap package"
	@echo "  flatpak    - Build Flatpak bundle"
	@echo "  appimage   - Build AppImage bundle"
	@echo "  everything - Build all packages"
	@echo "  clean      - Remove build artifacts"
	@echo ""
	@echo "Testing (requires Docker):"
	@echo "  test         - Run all package installation tests"
	@echo "  test-deb     - Test .deb package on Debian"
	@echo "  test-rpm     - Test .rpm package on Fedora"
	@echo "  test-apk     - Test .apk package on Alpine"
	@echo "  test-archlinux - Test Arch package on Arch Linux"
	@echo "  test-pip     - Test pip wheel on Debian"

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

all: deb rpm apk archlinux pip snap

everything: deb rpm apk archlinux pip flatpak appimage

clean:
	rm -rf dist result *.deb *.rpm *.apk *.pkg.tar.zst *.snap *.flatpak *.AppImage

 snap:
	@echo "Snap requires snapcraft (not in nixpkgs). Install with:"
	@echo "  sudo snap install snapcraft --classic"
	@echo "Then: cd snap && snapcraft"
	@command -v snapcraft 2>/dev/null || @echo "Note: snapcraft not installed - skipping"

flatpak:
	flatpak-builder --user --install build flatpak/com.github.whispaste.yml

appimage:
	./scripts/make-appimage.sh

# Testing targets (require Docker)
test:
	./tests/test-packages.sh

test-deb:
	./tests/test-packages.sh deb

test-rpm:
	./tests/test-packages.sh rpm

test-apk:
	./tests/test-packages.sh apk

test-archlinux:
	./tests/test-packages.sh archlinux

test-pip:
	./tests/test-packages.sh pip pip_sdist
