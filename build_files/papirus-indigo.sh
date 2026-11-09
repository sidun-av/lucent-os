#!/usr/bin/bash
# Papirus folders in Pebble Drift's indigo (called by design.sh; argument: the
# icons root, /usr/share/icons by default).
#
# Lucent draws its own folders (folder, Documents, Downloads, ..., Home, in
# /usr/share/icons/Lucent*, scalable). KDE apps never get past them for a
# folder: KIconLoader tries a name and its shorter fallbacks in Lucent before
# it looks at Papirus (folder-templates -> Lucent's folder), at every size.
# Papirus's folders show where a lookup reaches Papirus by the full name:
# GTK apps (GIMP, Inkscape) for names Lucent doesn't draw (Templates, Public,
# Git, network folders). Fedora 45's Papirus draws its 16 px places as
# monochrome text-colour glyphs; from 22 px up they come in colours, and the
# generic names point at blue:
#   folder-templates.svg -> folder-blue-templates.svg
# 1. Point those generic names at the indigo variant instead (what upstream's
#    papirus-folders tool does). Colour-named aliases and links into other
#    directories are left alone.
# 2. Recolour the indigo set to the Drift folder tokens of
#    docs/mockups/concepts-2026/pebble-drift/pebble-drift.css (back
#    --folder-back, front --folder-front-bottom (Papirus draws it flat; it is
#    also the whole 16 px folder), glyph --folder-glyph), so a folder has
#    the same colours at every size.
# Papirus is GPL-3.0; the recoloured files stay GPL-3.0 (THIRD_PARTY.md).
# Running it twice changes nothing.
set -euo pipefail
icons=${1:-/usr/share/icons}

retargeted=0
recoloured=0
for dir in "$icons"/Papirus*/*/places; do
    [ -d "$dir" ] && [ ! -L "$dir" ] || continue
    for link in "$dir"/*.svg; do
        [ -L "$link" ] || continue
        case "${link##*/}" in *-blue*|*-indigo*) continue ;; esac
        target=$(readlink "$link")
        case "$target" in */*) continue ;; *-blue*) ;; *) continue ;; esac
        indigo=${target/-blue/-indigo}
        if [ -f "$dir/$indigo" ]; then
            ln -sfn "$indigo" "$link"
            retargeted=$((retargeted + 1))
        fi
    done
    # Fedora's Papirus ships the 16 px generic folder.svg as a regular file
    # (a monochrome glyph) next to its folder-blue/folder-indigo family: it
    # becomes the indigo one too. Regular files without a blue and an
    # indigo twin (no colour family, or colour-named) stay as they are.
    for f in "$dir"/folder.svg "$dir"/folder-*.svg "$dir"/user-*.svg; do
        [ -f "$f" ] && [ ! -L "$f" ] || continue
        name=${f##*/}
        case "$name" in *-blue*|*-indigo*) continue ;; esac
        base=${name%.svg}
        stem=${base%%-*}                      # folder / user
        rest=${base#"$stem"}                  # "" or -templates, -home ...
        if [ -f "$dir/$stem-blue$rest.svg" ] && [ -f "$dir/$stem-indigo$rest.svg" ]; then
            ln -sfn "$stem-indigo$rest.svg" "$f"
            retargeted=$((retargeted + 1))
        fi
    done
    for f in "$dir"/*-indigo*.svg; do
        [ -f "$f" ] && [ ! -L "$f" ] || continue
        grep -qi -e '#3f51b5' -e '#5c6bc0' -e '#202543' "$f" || continue
        sed -e 's/#3[fF]51[bB]5/#4a5fe0/g' -e 's/#5[cC]6[bB][cC]0/#8496f5/g' -e 's/#202543/#2b3aa6/g' "$f" > "$f.lucent"
        cat "$f.lucent" > "$f"     # keep the file's owner and mode
        rm "$f.lucent"
        recoloured=$((recoloured + 1))
    done
done
echo "papirus-indigo: $retargeted names pointed at indigo, $recoloured indigo icons recoloured"
