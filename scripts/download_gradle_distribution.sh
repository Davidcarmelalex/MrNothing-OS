#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  printf 'usage: %s <pinned-version> <destination-zip>\n' "$0" >&2
  exit 64
fi

version="$1"
destination="$2"
case "$version" in
  8.9)
    expected_sha256="d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab"
    ;;
  *)
    printf 'unsupported Gradle distribution version: %s\n' "$version" >&2
    exit 64
    ;;
esac

if [[ -z "$destination" || "$destination" == "/" ]]; then
  printf 'invalid Gradle distribution destination\n' >&2
  exit 64
fi

destination_dir="$(dirname -- "$destination")"
mkdir -p -- "$destination_dir"
temporary_file="$(mktemp "$destination.part.XXXXXX")"
cleanup() {
  rm -f -- "$temporary_file"
}
trap cleanup EXIT

# All three hosts are Gradle-operated distribution endpoints. No community
# mirror or caller-supplied URL is accepted. Redirects are HTTPS-only.
urls=(
  "https://services.gradle.org/distributions/gradle-${version}-bin.zip"
  "https://downloads.gradle.org/distributions/gradle-${version}-bin.zip"
  "https://downloads.gradle-dn.com/distributions/gradle-${version}-bin.zip"
)

for url in "${urls[@]}"; do
  printf 'Downloading pinned Gradle %s from %s\n' "$version" "$url" >&2
  if ! curl \
    --fail \
    --location \
    --silent \
    --show-error \
    --proto '=https' \
    --proto-redir '=https' \
    --tlsv1.2 \
    --connect-timeout 20 \
    --max-time 180 \
    --retry 5 \
    --retry-connrefused \
    --retry-delay 5 \
    --retry-max-time 120 \
    --output "$temporary_file" \
    "$url"; then
    printf 'Download failed from %s; trying the next official endpoint.\n' "$url" >&2
    : > "$temporary_file"
    continue
  fi

  if ! printf '%s  %s\n' "$expected_sha256" "$temporary_file" | sha256sum --check --status; then
    printf 'SHA-256 mismatch for Gradle %s from %s; refusing extraction.\n' "$version" "$url" >&2
    exit 65
  fi

  mv -f -- "$temporary_file" "$destination"
  trap - EXIT
  printf 'Gradle %s distribution checksum verified.\n' "$version" >&2
  exit 0
done

printf 'All official Gradle distribution endpoints failed for %s.\n' "$version" >&2
exit 69
