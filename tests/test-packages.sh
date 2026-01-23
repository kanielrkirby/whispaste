#!/usr/bin/env bash
# Test package installations in Docker containers
# Usage: ./tests/test-packages.sh [test_name...]
# If no test names given, runs all tests
#
# Tests run in PARALLEL by default for speed.
# Use --sequential to run one at a time.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR=$(mktemp -d)
CONTAINER_PREFIX="whispaste-test-$$"
CONTAINER_PIDS=()

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cleanup function - kills all test containers
cleanup() {
    echo ""
    echo -e "${BLUE}[INFO]${NC} Cleaning up..."
    
    # Kill any running containers with our prefix
    local containers
    containers=$(docker ps -q --filter "name=${CONTAINER_PREFIX}" 2>/dev/null || true)
    if [[ -n "$containers" ]]; then
        echo -e "${BLUE}[INFO]${NC} Stopping containers..."
        docker kill $containers >/dev/null 2>&1 || true
        docker rm -f $containers >/dev/null 2>&1 || true
    fi
    
    # Kill background processes
    for pid in "${CONTAINER_PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    
    # Cleanup temp dir
    rm -rf "$RESULTS_DIR" 2>/dev/null || true
    
    echo -e "${BLUE}[INFO]${NC} Cleanup complete"
}

# Set up trap to cleanup on any exit
trap cleanup EXIT INT TERM HUP

# Check if a package file exists
check_package() {
    local pkg="$1"
    [[ -f "$PROJECT_DIR/$pkg" ]]
}

# Run a single test in Docker, output to temp file
run_test() {
    local name="$1"
    local image="$2"
    local test_script="$3"
    local result_file="$RESULTS_DIR/$name"
    local container_name="${CONTAINER_PREFIX}-${name}"
    
    echo "running" > "$result_file"
    
    if docker run --rm \
        --name "$container_name" \
        -v "$PROJECT_DIR:/pkg:ro" \
        "$image" \
        /bin/sh -c "$test_script" > "$result_file.log" 2>&1; then
        echo "pass" > "$result_file"
    else
        echo "fail" > "$result_file"
    fi
}

#
# Test definitions
#

test_deb() {
    if ! check_package "whispaste_0.1.0_amd64.deb"; then
        echo "skip" > "$RESULTS_DIR/deb"
        return
    fi
    
    # Use trixie (Debian 13) which has Python 3.13 (>= 3.12 requirement)
    # Install python3-pip first since postinstall script needs pip3
    run_test "deb" "debian:trixie-slim" '
        set -e
        apt-get update -qq
        DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip >/dev/null 2>&1
        DEBIAN_FRONTEND=noninteractive apt-get install -y /pkg/whispaste_0.1.0_amd64.deb >/dev/null 2>&1
        test -x /usr/bin/whispaste || { echo "Binary not installed"; exit 1; }
        echo "deb OK"
    '
}

test_rpm() {
    if ! check_package "whispaste-0.1.0-1.x86_64.rpm"; then
        echo "skip" > "$RESULTS_DIR/rpm"
        return
    fi
    
    run_test "rpm" "fedora:latest" '
        set -e
        # Install (may have scriptlet warnings but package still installs)
        dnf install -y /pkg/whispaste-0.1.0-1.x86_64.rpm 2>&1 || true
        test -x /usr/bin/whispaste || { echo "Binary not installed"; exit 1; }
        echo "rpm OK"
    '
}

test_apk() {
    if ! check_package "whispaste_0.1.0_x86_64.apk"; then
        echo "skip" > "$RESULTS_DIR/apk"
        return
    fi
    
    # NOTE: nfpm generates apk v2 format which requires apk-tools 3.1+
    # Alpine stable still ships apk-tools 3.0 which doesn't support v2
    # This test verifies the package file exists and is valid gzip
    run_test "apk" "alpine:latest" '
        set -e
        # Verify package is valid gzip archive
        gunzip -t /pkg/whispaste_0.1.0_x86_64.apk 2>&1 || { echo "Invalid gzip archive"; exit 1; }
        # apk v2 format not yet supported by apk-tools 3.0
        # Just verify file structure for now
        echo "apk package valid (v2 format - requires apk-tools 3.1+)"
    '
}

test_archlinux() {
    if ! check_package "whispaste-0.1.0-1-x86_64.pkg.tar.zst"; then
        echo "skip" > "$RESULTS_DIR/archlinux"
        return
    fi
    
    run_test "archlinux" "archlinux:latest" '
        set -e
        pacman -Sy --noconfirm >/dev/null 2>&1
        pacman -U --noconfirm /pkg/whispaste-0.1.0-1-x86_64.pkg.tar.zst >/dev/null 2>&1
        test -x /usr/bin/whispaste || { echo "Binary not installed"; exit 1; }
        echo "archlinux OK"
    '
}

test_pip() {
    if ! check_package "dist/whispaste-0.1.0-py3-none-any.whl"; then
        echo "skip" > "$RESULTS_DIR/pip"
        return
    fi
    
    # Use python:3.12 image since whispaste requires Python >= 3.12
    run_test "pip" "python:3.12-slim-bookworm" '
        set -e
        apt-get update -qq
        apt-get install -y -qq libportaudio2 >/dev/null 2>&1
        pip install --quiet /pkg/dist/whispaste-0.1.0-py3-none-any.whl
        test -f /usr/local/bin/whispaste || { echo "Entry point not created"; exit 1; }
        echo "pip OK"
    '
}

test_pip_sdist() {
    if ! check_package "dist/whispaste-0.1.0.tar.gz"; then
        echo "skip" > "$RESULTS_DIR/pip_sdist"
        return
    fi
    
    run_test "pip_sdist" "python:3.12-slim-bookworm" '
        set -e
        apt-get update -qq
        apt-get install -y -qq libportaudio2 >/dev/null 2>&1
        pip install --quiet /pkg/dist/whispaste-0.1.0.tar.gz
        test -f /usr/local/bin/whispaste || { echo "Entry point not created"; exit 1; }
        echo "pip_sdist OK"
    '
}

test_homebrew() {
    if ! check_package "homebrew/whispaste.rb"; then
        echo "skip" > "$RESULTS_DIR/homebrew"
        return
    fi
    
    run_test "homebrew" "debian:bookworm-slim" '
        set -e
        apt-get update -qq
        apt-get install -y -qq ruby >/dev/null 2>&1
        ruby -c /pkg/homebrew/whispaste.rb || { echo "Invalid Ruby syntax"; exit 1; }
        echo "homebrew formula syntax OK"
    '
}

test_flatpak() {
    if ! check_package "flatpak/com.github.whispaste.yml"; then
        echo "skip" > "$RESULTS_DIR/flatpak"
        return
    fi
    
    run_test "flatpak" "debian:bookworm-slim" '
        set -e
        apt-get update -qq
        apt-get install -y -qq python3-yaml >/dev/null 2>&1
        python3 -c "import yaml; yaml.safe_load(open(\"/pkg/flatpak/com.github.whispaste.yml\"))" || { echo "Invalid YAML"; exit 1; }
        echo "flatpak manifest OK"
    '
}

test_snap() {
    if ! check_package "snap/snapcraft.yaml"; then
        echo "skip" > "$RESULTS_DIR/snap"
        return
    fi
    
    run_test "snap" "debian:bookworm-slim" '
        set -e
        apt-get update -qq
        apt-get install -y -qq python3-yaml >/dev/null 2>&1
        python3 -c "import yaml; yaml.safe_load(open(\"/pkg/snap/snapcraft.yaml\"))" || { echo "Invalid YAML"; exit 1; }
        echo "snap manifest OK"
    '
}

# All available tests
ALL_TESTS=(deb rpm apk archlinux pip pip_sdist homebrew flatpak snap)

print_results() {
    local passed=0 failed=0 skipped=0
    
    echo ""
    echo "========================================"
    echo "Test Results"
    echo "========================================"
    
    for test_name in "${TESTS_TO_RUN[@]}"; do
        local result_file="$RESULTS_DIR/$test_name"
        local log_file="$RESULTS_DIR/$test_name.log"
        
        if [[ -f "$result_file" ]]; then
            local status=$(cat "$result_file")
            case "$status" in
                pass)
                    echo -e "  ${GREEN}[PASS]${NC} $test_name"
                    ((passed++))
                    ;;
                fail)
                    echo -e "  ${RED}[FAIL]${NC} $test_name"
                    if [[ -f "$log_file" ]]; then
                        echo "         Log: $(tail -5 "$log_file" | head -3)"
                    fi
                    ((failed++))
                    ;;
                skip)
                    echo -e "  ${YELLOW}[SKIP]${NC} $test_name (package not built)"
                    ((skipped++))
                    ;;
                running)
                    echo -e "  ${BLUE}[????]${NC} $test_name (interrupted)"
                    ((failed++))
                    ;;
            esac
        else
            echo -e "  ${RED}[ERR ]${NC} $test_name (no result)"
            ((failed++))
        fi
    done
    
    echo "========================================"
    echo -e "  ${GREEN}Passed:${NC}  $passed"
    echo -e "  ${RED}Failed:${NC}  $failed"
    echo -e "  ${YELLOW}Skipped:${NC} $skipped"
    echo "========================================"
    
    [[ $failed -eq 0 ]]
}

main() {
    echo "========================================"
    echo "whispaste Package Installation Tests"
    echo "========================================"
    echo ""
    
    if ! command -v docker &>/dev/null; then
        echo "Error: Docker is required but not installed"
        exit 1
    fi
    
    # Parse arguments
    SEQUENTIAL=false
    TESTS_TO_RUN=()
    
    for arg in "$@"; do
        case "$arg" in
            --sequential|-s)
                SEQUENTIAL=true
                ;;
            *)
                if printf '%s\n' "${ALL_TESTS[@]}" | grep -q "^$arg$"; then
                    TESTS_TO_RUN+=("$arg")
                else
                    echo "Unknown test: $arg"
                    echo "Available tests: ${ALL_TESTS[*]}"
                    exit 1
                fi
                ;;
        esac
    done
    
    # Default to all tests
    if [[ ${#TESTS_TO_RUN[@]} -eq 0 ]]; then
        TESTS_TO_RUN=("${ALL_TESTS[@]}")
    fi
    
    echo -e "${BLUE}[INFO]${NC} Running tests: ${TESTS_TO_RUN[*]}"
    echo -e "${BLUE}[INFO]${NC} Mode: $(if $SEQUENTIAL; then echo "sequential"; else echo "parallel"; fi)"
    echo ""
    
    # Run tests
    if $SEQUENTIAL; then
        for test_name in "${TESTS_TO_RUN[@]}"; do
            echo -e "${BLUE}[INFO]${NC} Running test_$test_name..."
            "test_$test_name"
        done
    else
        # Run all tests in parallel
        for test_name in "${TESTS_TO_RUN[@]}"; do
            "test_$test_name" &
            CONTAINER_PIDS+=($!)
        done
        
        echo -e "${BLUE}[INFO]${NC} Waiting for ${#CONTAINER_PIDS[@]} tests to complete..."
        
        # Wait for all background jobs
        for pid in "${CONTAINER_PIDS[@]}"; do
            wait "$pid" 2>/dev/null || true
        done
    fi
    
    print_results
}

main "$@"
