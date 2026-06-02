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

# cp -al: recursive hardlink copy (same inode, no extra disk). Kavita's scanner
# only descends into sub-directories, so a loose file at the library root is
# ignored — every download must land inside its own series folder. Kavita then
# groups and names series from each file's embedded ComicInfo.xml, so the
# original release names are left untouched.
if [ -d "$content" ]; then
  # Folder torrent: hardlink the release folder as-is (already a series folder).
  target="$dest/$(basename "$content")"
  [ -e "$target" ] && exit 0   # already linked → no-op (busybox cp has no -n)
  cp -al "$content" "$dest"/
else
  # Single-file torrent: wrap it in a folder named after the file so Kavita sees
  # a series directory rather than a stray file at the root.
  name=$(basename "$content")
  target="$dest/${name%.*}"
  [ -e "$target" ] && exit 0
  mkdir -p "$target"
  cp -al "$content" "$target"/
fi
