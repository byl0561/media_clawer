#!/usr/bin/env bash
# Recursively delete media_crawler marker files (alias.txt, checked_episode.txt)
# under a given root. These are the only on-disk inputs media_crawler reads
# beyond the standard nfo/poster set; deleting them resets all manual bindings
# and per-season "ignore-up-to" markers so you can re-bind cleanly.
#
# Default is dry-run (lists files only). Pass --apply to actually delete.
#
# Usage:
#   ./clean_media_marker_files.sh /mnt/nfs/media
#   ./clean_media_marker_files.sh /mnt/nfs/media --apply
set -euo pipefail

ROOT="${1:-}"
APPLY="no"
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY="yes" ;;
  esac
done

if [ -z "$ROOT" ] || [ ! -d "$ROOT" ]; then
  echo "用法: $0 <root_dir> [--apply]" >&2
  echo "  默认 dry-run，加 --apply 才真删" >&2
  exit 1
fi

echo "扫描 $ROOT 下的 alias.txt 和 checked_episode.txt ..."
MATCHES=$(find "$ROOT" -type f \( -name 'alias.txt' -o -name 'checked_episode.txt' \) 2>/dev/null || true)

if [ -z "$MATCHES" ]; then
  echo "没有找到。"
  exit 0
fi

echo "$MATCHES"
COUNT=$(echo "$MATCHES" | wc -l | tr -d ' ')
echo
echo "共 $COUNT 个文件。"

if [ "$APPLY" != "yes" ]; then
  echo "[DRY-RUN] 没有删除。确认无误后加 --apply 重跑。"
  exit 0
fi

echo "$MATCHES" | xargs -d '\n' rm -v
echo
echo "完成，已删除 $COUNT 个文件。"
