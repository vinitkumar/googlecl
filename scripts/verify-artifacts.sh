#!/usr/bin/env bash
# Check package payloads without installing or executing foreign binaries.
set -euo pipefail
cd "${1:-dist}"
if command -v sha256sum >/dev/null; then
  sha256sum -c checksums.txt
else
  shasum -a 256 -c checksums.txt
fi
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
shopt -s nullglob
archives=(*.tar.gz *.zip)
packages=(*.deb *.rpm)
test "${#archives[@]}" -eq 6
test "${#packages[@]}" -eq 4
for os in linux darwin windows; do
  for arch in amd64 arm64; do
    extension=tar.gz
    if [[ "$os" == windows ]]; then
      extension=zip
    fi
    matches=(*_"${os}_${arch}.$extension")
    test "${#matches[@]}" -eq 1
    archive=${matches[0]}
    target="$work/${os}_${arch}"
    mkdir -p "$target"
    if [[ "$os" == windows ]]; then
      unzip -q "$archive" -d "$target"
      suffix=.exe
    else
      tar -xzf "$archive" -C "$target"
      suffix=
    fi
    test -s "$target/google$suffix"
    test -s "$target/googlecl$suffix"
    cmp "$target/google$suffix" "$target/googlecl$suffix"
    for doc in LICENSE README.md docs/authentication.md docs/compatibility.md docs/releasing.md; do
      test -s "$target/$doc"
    done
    echo "Verified $archive (both executables identical)"
  done
done
for package in "${packages[@]}"; do
  case "$package" in
    *.deb)
      dpkg-deb --info "$package"
      dpkg-deb --contents "$package" > "$work/payload"
      ;;
    *.rpm)
      if command -v rpm >/dev/null; then
        rpm -qip "$package"
        rpm -qlp "$package" > "$work/payload"
      else
        bsdtar -tf "$package" > "$work/payload"
      fi
      ;;
  esac
  grep -E '(^|[[:space:]])\.?/?usr/bin/google$' "$work/payload"
  grep -E '(^|[[:space:]])\.?/?usr/bin/googlecl$' "$work/payload"
  echo "Verified $package payload"
done
