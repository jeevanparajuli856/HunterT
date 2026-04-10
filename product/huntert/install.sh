#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
product_root="${script_dir}"
repo_root="$(cd -- "${product_root}/../.." && pwd)"
install_dir="${HUNTERT_INSTALL_DIR:-$HOME/.local/bin}"
binary_dir="${product_root}/bin"
binary_path="${binary_dir}/HunterT"

go_bin="${GO_BIN:-}"
if [[ -z "${go_bin}" ]]; then
  if command -v go >/dev/null 2>&1; then
    go_bin="$(command -v go)"
  elif [[ -x /usr/local/go/bin/go ]]; then
    go_bin="/usr/local/go/bin/go"
  else
    echo "go was not found. Install Go 1.22+ or set GO_BIN." >&2
    exit 1
  fi
fi

mkdir -p "${binary_dir}" "${install_dir}"

echo "Building HunterT with ${go_bin}..."
(
  cd "${product_root}"
  "${go_bin}" build -o "${binary_path}" ./cmd/huntert
)

launcher_path="${install_dir}/HunterT"
cat > "${launcher_path}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export HUNTERT_REPO_ROOT="${repo_root}"
export HUNTERT_PRODUCT_ROOT="${product_root}"
exec "${binary_path}" "\$@"
EOF
chmod +x "${launcher_path}"

ln -sf "HunterT" "${install_dir}/huntert"

echo
echo "HunterT installed."
echo "  launcher: ${launcher_path}"
echo "  alias:    ${install_dir}/huntert"
echo
if [[ ":${PATH}:" != *":${install_dir}:"* ]]; then
  echo "Add this to your shell profile if needed:"
  echo "  export PATH=\"${install_dir}:\$PATH\""
  echo
fi
echo "Run:"
echo "  HunterT version"
