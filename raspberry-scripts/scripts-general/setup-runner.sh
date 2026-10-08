#!/bin/bash
# Script para instalar e configurar GitHub Actions Runner no Raspberry Pi
set -euo pipefail

# === Configurações ===
ORG="douglasdalves"
REPO="automation"
RUNNER_USER="dalves"
RUNNER_DIR="/home/$RUNNER_USER/actions-runner"
LABELS="homelab"
RUNNER_VERSION="2.337.0"
RUNNER_ARCHIVE="actions-runner-linux-arm64-$RUNNER_VERSION.tar.gz"
RUNNER_SHA256="9b1dc70626422526e3c94767cf024896beb15da5342a3f4819bf2feac13e0393"

# === Criar usuário dedicado ===
if ! id "$RUNNER_USER" &>/dev/null; then
  sudo adduser --disabled-password --gecos "" "$RUNNER_USER"
fi

# === Instalar dependências ===
sudo apt update
sudo apt install -y curl tar

# === Criar diretório do runner ===
RUNNER_GROUP="$(id -gn "$RUNNER_USER")"
sudo install -d -o "$RUNNER_USER" -g "$RUNNER_GROUP" -m 0750 "$RUNNER_DIR"

# === Baixar e extrair runner ===
if ! sudo -u "$RUNNER_USER" -- test -x "$RUNNER_DIR/config.sh"; then
  RUNNER_ARCHIVE_PATH="$RUNNER_DIR/$RUNNER_ARCHIVE"
  sudo -u "$RUNNER_USER" -- curl --fail --location --silent --show-error \
    "https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/$RUNNER_ARCHIVE" \
    --output "$RUNNER_ARCHIVE_PATH"
  printf '%s  %s\n' "$RUNNER_SHA256" "$RUNNER_ARCHIVE_PATH" | sudo sha256sum --check -
  sudo -u "$RUNNER_USER" -- tar -xzf "$RUNNER_ARCHIVE_PATH" -C "$RUNNER_DIR"
fi

# === Configurar runner ===
if sudo -u "$RUNNER_USER" -- test -f "$RUNNER_DIR/.runner"; then
  echo "Runner já configurado; mantendo o registro existente."
else
  if [[ -z "${RUNNER_TOKEN:-}" ]]; then
    read -r -s -p "GitHub runner registration token: " RUNNER_TOKEN
    printf '\n'
  fi

  if [[ -z "$RUNNER_TOKEN" ]]; then
    echo "Erro: o token de registro do runner não pode estar vazio." >&2
    exit 1
  fi

  sudo -u "$RUNNER_USER" -- bash -c '
    cd "$1"
    shift
    exec ./config.sh "$@"
  ' _ "$RUNNER_DIR" \
    --url "https://github.com/$ORG/$REPO" \
    --token "$RUNNER_TOKEN" \
    --labels "$LABELS" \
    --unattended
  unset RUNNER_TOKEN
fi

# === Instalar e iniciar como serviço ===
sudo bash -c 'cd "$1"; shift; exec ./svc.sh install "$@"' _ "$RUNNER_DIR" "$RUNNER_USER"
sudo bash -c 'cd "$1"; exec ./svc.sh start' _ "$RUNNER_DIR"
sudo bash -c 'cd "$1"; exec ./svc.sh status' _ "$RUNNER_DIR"
