#!/usr/bin/bash
# Test for papirus-indigo.sh on a small fake Papirus tree; design.sh runs it
# before touching the real one:  papirus-indigo-test.sh path/to/papirus-indigo.sh
set -euo pipefail
script=$1
t=$(mktemp -d)
trap 'rm -rf "$t"' EXIT
mk() {  # dir file: an icon in Papirus's indigo colours
    printf '<svg><path style="fill:#3f51b5"/><rect style="fill:#5C6BC0"/><path style="fill:#202543"/></svg>\n' > "$1/$2"
}
for v in Papirus/64x64 Papirus/16x16 Papirus-Dark/16x16; do
    d=$t/$v/places; mkdir -p "$d"
    for c in blue indigo red; do mk "$d" "folder-$c.svg"; mk "$d" "folder-$c-templates.svg"; mk "$d" "user-$c-home.svg"; done
    mk "$d" folder-blue-onlyblue.svg
    ln -s folder-blue.svg "$d/folder.svg"
    ln -s folder-blue-templates.svg "$d/folder-templates.svg"
    ln -s user-blue-home.svg "$d/user-home.svg"
    ln -s folder-blue-onlyblue.svg "$d/folder-onlyblue.svg"     # no indigo variant: stays blue
    ln -s folder-red.svg "$d/folder-important.svg"              # not blue: untouched
    ln -s folder-blue.svg "$d/folder-blue-open.svg"             # a blue-named alias: untouched
    ln -s ../../Papirus/64x64/places/folder-blue.svg "$d/folder-elsewhere.svg"  # other dir: untouched
done
mkdir -p "$t/Papirus-Light/64x64"; ln -s ../../Papirus/64x64/places "$t/Papirus-Light/64x64/places"
# Fedora's Papirus at 16 px: the generic folder.svg is a regular file (a
# monochrome glyph), not a link to folder-blue.svg; folder-templates.svg is
# regular too but has no colour family at that size.
d=$t/Papirus/22x22/places; mkdir -p "$d"
for c in blue indigo; do mk "$d" "folder-$c.svg"; done
printf '<svg><path class="ColorScheme-Text"/></svg>\n' > "$d/folder.svg"
printf '<svg><path class="ColorScheme-Text"/></svg>\n' > "$d/folder-templates.svg"
mk "$d" folder-red.svg

bash "$script" "$t"

fail=0
check() { if ! eval "$1"; then echo "FAIL: $1"; fail=1; fi; }
for v in Papirus/64x64 Papirus/16x16 Papirus-Dark/16x16; do
    d=$t/$v/places
    check "[ \"\$(readlink $d/folder.svg)\" = folder-indigo.svg ]"
    check "[ \"\$(readlink $d/folder-templates.svg)\" = folder-indigo-templates.svg ]"
    check "[ \"\$(readlink $d/user-home.svg)\" = user-indigo-home.svg ]"
    check "[ \"\$(readlink $d/folder-onlyblue.svg)\" = folder-blue-onlyblue.svg ]"
    check "[ \"\$(readlink $d/folder-important.svg)\" = folder-red.svg ]"
    check "[ \"\$(readlink $d/folder-blue-open.svg)\" = folder-blue.svg ]"
    check "[ \"\$(readlink $d/folder-elsewhere.svg)\" = ../../Papirus/64x64/places/folder-blue.svg ]"
    # the indigo set gets the Drift folder colours, other colours keep theirs
    check "grep -q 'fill:#4a5fe0' $d/folder-indigo-templates.svg"
    check "grep -q 'fill:#8496f5' $d/folder-indigo-templates.svg"
    check "grep -q 'fill:#2b3aa6' $d/folder-indigo-templates.svg"
    check "! grep -qi '#3f51b5\\|#5c6bc0\\|#202543' $d/folder-indigo.svg"
    check "grep -q 'fill:#3f51b5' $d/folder-red.svg"
    check "grep -q 'fill:#3f51b5' $d/folder-blue.svg"
done
# a regular generic file with blue and indigo twins becomes the indigo one;
# without a colour family (or colour-named) it stays as it is
d=$t/Papirus/22x22/places
check "[ \"\$(readlink $d/folder.svg)\" = folder-indigo.svg ]"
check "[ -f $d/folder-templates.svg ] && [ ! -L $d/folder-templates.svg ]"
check "[ -f $d/folder-red.svg ] && [ ! -L $d/folder-red.svg ]"
# running it twice changes nothing
before=$(find "$t" -type l -exec readlink {} + | sort | md5sum; find "$t" -type f -name "*.svg" -exec cat {} + | md5sum)
bash "$script" "$t"
after=$(find "$t" -type l -exec readlink {} + | sort | md5sum; find "$t" -type f -name "*.svg" -exec cat {} + | md5sum)
check "[ \"$before\" = \"$after\" ]"
[ $fail = 0 ] && echo "papirus-indigo: all checks passed"
exit $fail
