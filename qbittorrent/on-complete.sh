#!/bin/sh
# Hardlink a finished book/comic/manga download into its Kavita library so the
# torrent keeps seeding from /data/torrents while Kavita reads /data/media.
# Same inode on both sides, so this costs no extra disk space.
#
# Wired by the bootstrap as qBittorrent's "run on torrent finished" program
# (see scripts/bootstrap/modules/qbittorrent_setup.py):
#   /bin/sh /scripts/on-complete.sh "%F" "%L"
#     $1 = %F  full content path (a file for single-file torrents, else a folder)
#     $2 = %L  category
#
# Movies and TV are imported by Radarr/Sonarr, so only the book categories are
# handled here; anything else exits without doing work.
content="$1"
category="$2"

case "$category" in
  bd)     dest="/data/media/books/bd" ;;
  comics) dest="/data/media/books/comics" ;;
  manga)  dest="/data/media/books/manga" ;;
  livres) dest="/data/media/books/livres" ;;
  *)      exit 0 ;;
esac

[ -e "$content" ] || exit 0
mkdir -p "$dest"
# Skip if already linked, so re-running on the same torrent is a no-op (and to
# stay portable: busybox cp has no --no-clobber).
target="$dest/$(basename "$content")"
[ -e "$target" ] && exit 0
# cp -al: recursive hardlink copy (same inode, no extra disk). Kavita groups and
# names series from each file's embedded ComicInfo.xml, so the original release
# names are left untouched.
cp -al "$content" "$dest"/
