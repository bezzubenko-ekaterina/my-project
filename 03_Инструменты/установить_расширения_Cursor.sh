#!/usr/bin/env bash
# Установка расширений из 02_инструкция.md (Russian Pack, Prettier, GitLens, Live Server).
#
# Почему не через `cursor --install-extension id`:
# - CLI часто «висит» на Marketplace.
# - Свежий Russian Language Pack требует VS Code новее, чем движок внутри Cursor — нужна
#   версия языкового пакета с тем же major.minor, что и "vscodeVersion" в product.json.
#
# Запуск в Terminal.app:
#   cd "/Users/sergej/Documents/My Project/03_Инструменты"
#   chmod +x установить_расширения_Cursor.sh && ./установить_расширения_Cursor.sh

set -euo pipefail

CURSOR_APP="/Applications/Cursor.app"
CURSOR_CLI="${CURSOR_APP}/Contents/Resources/app/bin/cursor"
PRODUCT_JSON="${CURSOR_APP}/Contents/Resources/app/product.json"

if [[ ! -x "$CURSOR_CLI" ]]; then
  echo "Не найден Cursor: $CURSOR_CLI"
  exit 1
fi

# Версия движка VS Code внутри Cursor (например 1.105.1)
VSCODE_VER=$(python3 -c "import json; print(json.load(open('$PRODUCT_JSON'))['vscodeVersion'])")
VSCODE_MM=$(echo "$VSCODE_VER" | cut -d. -f1-2)

echo "Cursor CLI: $CURSOR_CLI"
echo "VS Code engine в Cursor: $VSCODE_VER (ищем языковой пакет с префиксом $VSCODE_MM.)"
echo

install_vsix_from_url() {
  local label="$1"
  local url="$2"
  local tmp_dir tmp_gz tmp_vsix
  # macOS mktemp: в имени шаблона «X» должны быть в самом конце (нельзя mktemp …XXXXXX.vsix).
  tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/cursor_ext_install.XXXXXX")
  tmp_gz="${tmp_dir}/download.gz"
  tmp_vsix="${tmp_dir}/extension.vsix"
  echo "=== $label ==="
  echo "Скачивание..."
  curl -sSL --fail --max-time 120 -o "$tmp_gz" "$url"
  gunzip -c "$tmp_gz" > "$tmp_vsix"
  rm -f "$tmp_gz"
  if [[ ! -s "$tmp_vsix" ]]; then
    echo "Ошибка: после распаковки VSIX пустой или не создан."
    rm -rf "$tmp_dir"
    return 1
  fi
  echo "Установка из VSIX..."
  if ! "$CURSOR_CLI" --install-extension "$tmp_vsix" --force; then
    rm -rf "$tmp_dir"
    return 1
  fi
  rm -rf "$tmp_dir"
  echo
}

# Совместимая версия Russian Language Pack (первая в списке Marketplace с префиксом 1.105. и т.д.)
LANG_VER=$(curl -sS -X POST "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json;api-version=7.1-preview.1" \
  -d '{"filters":[{"criteria":[{"filterType":7,"value":"ms-ceintl.vscode-language-pack-ru"}],"pageSize":200}],"flags":439}' \
  | python3 -c "import sys, json; mm=sys.argv[1]; d=json.load(sys.stdin); vers=[v['version'] for v in d['results'][0]['extensions'][0]['versions']]; m=[v for v in vers if v.startswith(mm+'.')]; print(m[0] if m else vers[0])" "$VSCODE_MM")

echo "Версия Russian Language Pack: $LANG_VER"
LANG_URL="https://marketplace.visualstudio.com/_apis/public/gallery/publishers/ms-ceintl/vsextensions/vscode-language-pack-ru/${LANG_VER}/vspackage"
install_vsix_from_url "Russian Language Pack" "$LANG_URL"

install_vsix_from_url "Prettier" \
  "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/esbenp/vsextensions/prettier-vscode/latest/vspackage"

install_vsix_from_url "GitLens" \
  "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/eamodio/vsextensions/gitlens/latest/vspackage"

install_vsix_from_url "Live Server" \
  "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/ritwickdey/vsextensions/LiveServer/latest/vspackage"

echo "Готово."
echo "Русский язык: Cmd+Shift+P → «Configure Display Language» → ru → перезапуск Cursor."
