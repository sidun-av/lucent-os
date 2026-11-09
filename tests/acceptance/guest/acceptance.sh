#!/usr/bin/bash
# Lucent OS acceptance test, guest side. TEST-ONLY.
#
# Runs as root on the freshly installed system, started by
# lucent-acceptance.service, which only the acceptance kickstart
# (tests/acceptance/test.ks) adds to a throw-away test install. The host
# (tests/acceptance/harness.py) answers requests on a virtio-serial port:
# screenshots, and keyboard/pointer input through QEMU, i.e. real input
# arriving through KWin. What the user does runs as the user inside the
# Plasma session: through the session's systemd --user manager, whose
# environment is the session's (WAYLAND_DISPLAY, DISPLAY, XDG_*), the way
# KRunner and Dolphin start programs.
#
#   acceptance.sh PAYLOAD_DIR
# Writes PAYLOAD_DIR/results/{results.tsv,metrics.tsv,logs/} (results also
# stream to the host), sends DONE and powers the machine off.
set -uo pipefail

P=$1
OUT=$P/results
LOGS=$OUT/logs
mkdir -p "$LOGS"
: > "$OUT/results.tsv"
: > "$OUT/metrics.tsv"
U=anna
NPP=npp.8.9.9.Installer.x64.exe
NPP_SHA256=a18cfb33d616c8eecda0059604d40bdb9d607fbc4ede857c8be6e41986464367
BIN=/var/lib/lucent-acceptance
mkdir -p "$BIN"
install -m 0644 "$P/guest/kwin.py" "$BIN/kwin.py"
restorecon -R "$BIN" 2>/dev/null || true
FAILED=0

PORT=/dev/virtio-ports/org.lucent.acceptance

up() { cut -d' ' -f1 /proc/uptime; }
log() { printf '[%8s] %s\n' "$(up)" "$*" >> "$LOGS/acceptance.log"; }
oneline() { tr '\n\t' '  ' | cut -c1-700; }
ctl() {
    # The port is opened per request, so no program the test starts inherits
    # it (one in another SELinux domain would log an AVC for it).
    local reply=""
    exec 3<>"$PORT"
    printf '%s\n' "$*" >&3
    IFS= read -r -t 180 reply <&3 || reply=TIMEOUT
    exec 3>&-
    local req="$*"
    log "ctl: ${req:0:160} -> $reply"
    printf '%s' "$reply"
}
record() { # id PASS|FAIL|INFO detail
    local detail
    detail=$(printf '%s' "${3:-}" | oneline)
    printf '%s\t%s\t%s\n' "$1" "$2" "$detail" >> "$OUT/results.tsv"
    ctl "RESULT $2 $1: $detail" >/dev/null
    [ "$2" = FAIL ] && FAILED=1
    return 0
}
metric() { # key value
    local v
    v=$(printf '%s' "$2" | oneline)
    printf '%s\t%s\n' "$1" "$v" >> "$OUT/metrics.tsv"
    ctl "METRIC $1 $v" >/dev/null
}
shot() { ctl "SHOT $1" >/dev/null; }
keys() { ctl "KEYS $*" >/dev/null; }
typetext() { ctl "TYPE $*" >/dev/null; }
click() { ctl "CLICK $1 $2" >/dev/null; }

finished=0
finish() {
    ((finished)) && return
    finished=1
    log "collecting system logs"
    journalctl -b --no-pager -o short-monotonic > "$LOGS/journal.txt" 2>&1
    systemctl list-units --failed --no-pager > "$LOGS/failed-units.txt" 2>&1
    as_user journalctl --user -b --no-pager -o short-monotonic 2>/dev/null | cat > "$LOGS/journal-user.txt"
    ls -la "$BIN" "${HOMEDIR:-/nonexistent}/.local/share/applications" > "$LOGS/files.txt" 2>&1
    sync
    ctl "DONE $FAILED" >/dev/null
    sync
    systemctl poweroff --no-block
}
trap finish EXIT

as_user() { # run inside the Plasma session (the user's systemd manager)
    # --pipe hands our stdio to the unit over D-Bus, and the bus may not
    # touch files on the payload disk (an AVC): stdout always goes through a
    # pipe, and callers send stderr only to /dev/null or leave it alone (the
    # journal). systemd-run fails with "Bad message" when stderr is the same
    # pipe as stdout (2>&1) or stdin is redirected.
    systemd-run --quiet --user --machine="$U@.host" --wait --pipe --collect \
        -p RuntimeMaxSec=600 -- "$@" | cat
    return "${PIPESTATUS[0]}"
}
kwin() { as_user /usr/bin/python3 -I "$BIN/kwin.py" "$@"; }   # errors: the journal
# First usable window whose caption matches the ERE $1 (TSV, see kwin.py).
find_window() { kwin list | RE=$1 awk -F'\t' '$9 == 1 && $1 ~ ENVIRON["RE"]' | head -n1; }
find_class() { kwin list | C=$1 awk -F'\t' '$9 == 1 && tolower($2) == tolower(ENVIRON["C"])' | head -n1; }
wait_until() { # seconds command... (polls every second)
    local deadline=$((SECONDS + $1)); shift
    while ((SECONDS < deadline)); do "$@" && return 0; sleep 1; done
    return 1
}
user_pids() { pgrep -u "$U" -f "$1" 2>/dev/null; }
cgroup_of() { cat "/proc/$1/cgroup" 2>/dev/null | oneline; }

log "acceptance test starting"
metric os "$(. /etc/os-release; echo "$PRETTY_NAME")"
metric kernel "$(uname -r)"
metric lucent_bridge "$(lucent-bridge --version 2>&1)"
metric wine "$(wine --version 2>&1)"
metric cpu "$(nproc) vCPU, $(sed -n 's/^model name.*: //p' /proc/cpuinfo | head -n1)"
metric deployment "$(rpm-ostree status --booted 2>/dev/null | grep -m1 -E 'Digest|Version|ostree-image' | sed 's/^ *//')"

# ---------------------------------------------------------------------------
# 1. The Plasma session (autologin)
# ---------------------------------------------------------------------------
HOMEDIR=$(getent passwd "$U" | cut -d: -f6)
session_up() {
    pgrep -u "$U" -x plasmashell >/dev/null &&
        as_user sh -c 'test -n "${WAYLAND_DISPLAY:-}"' 2>/dev/null
}
if wait_until 600 session_up; then
    login_up=$(up)
    record session.plasma PASS "Plasma session of $U running ${login_up} s after kernel start (autologin)"
else
    record session.plasma FAIL "no Plasma session for $U after 10 min"
    loginctl list-sessions > "$LOGS/sessions.txt" 2>&1
    shot 00-no-session
    exit 1
fi
as_user systemctl --user show-environment 2>/dev/null | cat > "$LOGS/session-environment.txt"
# A test sits idle for minutes (waiting for the template): keep the screen
# on and unlocked, as a user working at the machine would.
if systemd-run --quiet --user --machine="$U@.host" --unit=lucent-acceptance-inhibit --collect \
        -- kde-inhibit --power --screenSaver sleep infinity < /dev/null 2>/dev/null; then
    record session.inhibit INFO "screen locking and power management inhibited for the test (kde-inhibit)"
else
    record session.inhibit INFO "kde-inhibit unavailable; the screen may lock while the test waits"
fi
loginctl show-session "$(loginctl list-sessions --no-legend | awk -v u="$U" '$3 == u {print $1; exit}')" \
    > "$LOGS/session.txt" 2>&1
sleep 25
shot 01-desktop-after-login

# ---------------------------------------------------------------------------
# 2. Idle numbers, 2 min after login
# ---------------------------------------------------------------------------
target=$(awk -v l="$login_up" 'BEGIN { print l + 120 }')
while awk -v u="$(up)" -v t="$target" 'BEGIN { exit !(u < t) }'; do sleep 2; done
read -r mem_total mem_avail < <(awk '/^MemTotal:/ {t=$2} /^MemAvailable:/ {a=$2} END {print t, a}' /proc/meminfo)
metric ram_total_mib $((mem_total / 1024))
metric ram_used_idle_mib $(((mem_total - mem_avail) / 1024))
free -m > "$LOGS/free.txt"
ps -eo rss,user,comm --sort=-rss | head -n 30 > "$LOGS/top-rss.txt"
sys_services=$(systemctl list-units --type=service --state=running --no-legend --plain | grep -vc '^lucent-acceptance')
user_services=$(as_user systemctl --user list-units --type=service --state=running --no-legend --plain | grep -vc '^run-')
systemctl list-units --type=service --state=running --no-legend --plain > "$LOGS/services-system.txt"
as_user systemctl --user list-units --type=service --state=running --no-legend --plain > "$LOGS/services-user.txt"
metric services_running_system "$sys_services"
metric services_running_user "$user_services"
sa=""
for _ in $(seq 60); do sa=$(systemd-analyze 2>&1) && break; sleep 5; done
metric systemd_analyze "$(head -n1 <<<"$sa")"
metric graphical_target "$(grep -o 'graphical.target reached after .*' <<<"$sa")"
systemd-analyze blame --no-pager > "$LOGS/systemd-analyze-blame.txt" 2>&1
systemd-analyze critical-chain --no-pager > "$LOGS/systemd-analyze-critical-chain.txt" 2>&1
read -r disk_size disk_used < <(df -B1 --output=size,used /sysroot | tail -n1)
metric disk_size_gb "$(awk -v b="$disk_size" 'BEGIN { printf "%.1f", b / 1e9 }')"
metric disk_used_gb "$(awk -v b="$disk_used" 'BEGIN { printf "%.1f", b / 1e9 }')"
metric flatpak_apps_gb "$(du -sxB1 /var/lib/flatpak 2>/dev/null | awk '{ printf "%.1f", $1 / 1e9 }')"
metric filesystem "$(findmnt -no FSTYPE /sysroot)"
df -h > "$LOGS/df.txt"

# ---------------------------------------------------------------------------
# 3. The offline apps: installed, among the launcher's favorites, in the launcher
# ---------------------------------------------------------------------------
mapfile -t APPS < <(grep -Ev '^[[:space:]]*(#|$)' "$P/flatpaks.list")
installed=$(flatpak list --system --app --columns=application 2>&1)
printf '%s\n' "$installed" > "$LOGS/flatpak-list.txt"
xml=/usr/share/plasma/plasmoids/org.lucent.launcher/contents/config/main.xml
pinned=$(sed -n 's:.*<default>\(.*\)</default>.*:\1:p' "$xml" | head -n1)
override=$(grep -h '^pinned=' "$HOMEDIR/.config/plasma-org.kde.plasma.desktop-appletsrc" 2>/dev/null | head -n1)
[ -n "$override" ] && pinned=${override#pinned=}
menu=$(as_user kbuildsycoca6 --menutest 2>/dev/null)
printf '%s\n' "$menu" > "$LOGS/menutest.txt"
session_dirs=$(sed -n 's/^XDG_DATA_DIRS=//p' "$LOGS/session-environment.txt")
miss_inst=() miss_pin=() miss_menu=()
for a in "${APPS[@]}"; do
    grep -qx "$a" <<<"$installed" || miss_inst+=("$a")
    [[ ",$pinned," == *",$a.desktop,"* ]] || miss_pin+=("$a")
    if [ -n "$menu" ]; then
        grep -qF "$a.desktop" <<<"$menu" || miss_menu+=("$a")
    else
        # No menu test: the session must see Flatpak's exported entries.
        [[ ":$session_dirs:" == *:/var/lib/flatpak/exports/share:* || ":$session_dirs:" == *:/var/lib/flatpak/exports/share/:* ]] &&
            [ -f "/var/lib/flatpak/exports/share/applications/$a.desktop" ] || miss_menu+=("$a")
    fi
done
n=${#APPS[@]}
if ((n == 10 && ${#miss_inst[@]} == 0)); then
    record apps.installed PASS "all $n apps installed system-wide from the ISO, no network: ${APPS[*]}"
else
    record apps.installed FAIL "expected 10 apps, list has $n; missing: ${miss_inst[*]:-none}"
fi
if ((${#miss_pin[@]} == 0)); then
    record apps.favorites PASS "all $n in the launcher's pinned favorites (first under All apps)"
else
    record apps.favorites FAIL "not pinned: ${miss_pin[*]}"
fi
how=$([ -n "$menu" ] && echo "kbuildsycoca6 --menutest, the KService menu the launcher reads" || echo "session XDG_DATA_DIRS + exported entries")
if ((${#miss_menu[@]} == 0)); then
    record apps.launcher PASS "all $n in the session's application menu ($how)"
else
    record apps.launcher FAIL "not in the menu ($how): ${miss_menu[*]}"
fi
keys meta
sleep 5
shot 02-launcher-offline-apps
keys esc
sleep 2

# ---------------------------------------------------------------------------
# 4. lucent-bridge's prefix template, built by its timer after boot
# ---------------------------------------------------------------------------
tpl_done() { [ "$(systemctl show -p ExecMainExitTimestampMonotonic --value lucent-bridge-template.service)" != 0 ]; }
wait_until 600 tpl_done
res=$(systemctl show -p Result --value lucent-bridge-template.service)
status=$(systemctl show -p ExecMainStatus --value lucent-bridge-template.service)
t_start=$(systemctl show -p ExecMainStartTimestampMonotonic --value lucent-bridge-template.service)
t_exit=$(systemctl show -p ExecMainExitTimestampMonotonic --value lucent-bridge-template.service)
secs() { awk -v u="$1" 'BEGIN { printf "%.0f", u / 1e6 }'; }
journalctl -b -u lucent-bridge-template.service -u lucent-bridge-template.timer --no-pager > "$LOGS/template.txt" 2>&1
metric template_started_s "$(secs "$t_start")"
metric template_finished_s "$(secs "$t_exit")"
metric template_size "$(du -sh /var/lib/lucent-bridge/prefix-template 2>/dev/null | cut -f1)"
if [ "$res" = success ] && [ "$status" = 0 ] && [ "$t_exit" != 0 ] &&
   [ -f /usr/share/lucent-bridge/prefix-template/system.reg ] && (($(secs "$t_exit") <= 330)); then
    record template.service PASS "lucent-bridge-template.service succeeded: started $(secs "$t_start") s, finished $(secs "$t_exit") s after kernel start"
else
    record template.service FAIL "result=$res status=$status started=$(secs "$t_start") s finished=$(secs "$t_exit") s (limit 330 s); see logs/template.txt"
fi

# ---------------------------------------------------------------------------
# 5. The Windows flow, as the user: download, double-click, install, launch
# ---------------------------------------------------------------------------
flow_start=$(date +%s)
DL=$(as_user xdg-user-dir DOWNLOAD)
[ -n "$DL" ] && [ "$DL" != "$HOMEDIR" ] || DL=$HOMEDIR/Downloads
as_user mkdir -p "$DL"
# The "download": the user copies it in (owner and SELinux label as for a browser download).
as_user cp "$P/$NPP" "$DL/$NPP"
if echo "$NPP_SHA256  $DL/$NPP" | sha256sum -c --quiet; then
    record exe.download PASS "$DL/$NPP ($(stat -c %s "$DL/$NPP") bytes, SHA-256 as pinned in lucent-bridge's E2E, $(ls -Z "$DL/$NPP" | cut -d' ' -f1))"
else
    record exe.download FAIL "installer missing or hash mismatch"
fi
mime=$(as_user kmimetypefinder "$DL/$NPP" 2>/dev/null | head -n1)
[ -n "$mime" ] || mime=$(as_user xdg-mime query filetype "$DL/$NPP" 2>/dev/null)
default=$(as_user xdg-mime query default "$mime" 2>/dev/null)
gio_default=$(as_user gio mime "$mime" 2>/dev/null | sed -n 's/^Default application for .*: //p')
if [ "$gio_default" = lucent-bridge.desktop ] || [ "$default" = lucent-bridge.desktop ]; then
    record exe.handler PASS "type $mime; default application: xdg-mime '${default:-?}', gio '${gio_default:-?}'"
else
    record exe.handler FAIL "type '$mime'; default application: xdg-mime '${default:-?}', gio '${gio_default:-?}'"
fi

opener=""
for c in kioclient kioclient6; do
    as_user sh -c "command -v $c" >/dev/null 2>&1 && opener=$c && break
done
# What a double-click in Dolphin does: KIO's OpenUrlJob for the file.
log "opening $DL/$NPP with ${opener:-gio open}"
if [ -n "$opener" ]; then
    as_user "$opener" exec "$DL/$NPP" 2>/dev/null | cat > "$LOGS/open.txt"
else
    as_user gio open "$DL/$NPP" 2>/dev/null | cat > "$LOGS/open.txt"
fi
bridge_pid() { user_pids "lucent-bridge run .*${NPP//./\\.}" | head -n1; }
if wait_until 60 bridge_pid; then
    bp=$(bridge_pid)
    cg=$(cgroup_of "$bp")
    args=$(tr '\0' ' ' < "/proc/$bp/cmdline")
    if [[ "$cg" == *'app-lucent\x2dbridge'* ]]; then
        record exe.opened-with-bridge PASS "${opener:-gio} exec -> '$args', in $cg (KIO started lucent-bridge.desktop)"
    else
        record exe.opened-with-bridge FAIL "lucent-bridge runs ('$args') but not as lucent-bridge.desktop: $cg"
    fi
else
    record exe.opened-with-bridge FAIL "no lucent-bridge process 60 s after '${opener:-gio} exec'; $(oneline < "$LOGS/open.txt")"
fi

# The installer's own GUI: the default button on every page, as a user would.
INST_RE='^(Installer Language|Notepad\+\+ .*Setup)'
PROMPT_RE='^Wine (Mono|Gecko) Installer'
installer_alive() {
    local p
    for p in $(user_pids "${NPP//./\\.}"); do
        [ "$(cat "/proc/$p/comm" 2>/dev/null)" != lucent-bridge ] && return 0
    done
    return 1
}
# Wait for the installer's window (lucent-bridge may first set up the
# Windows environment). Wine must never ask to download anything.
t_inst=$SECONDS prompted=""
while ((SECONDS - t_inst < 600)); do
    find_window "$INST_RE" | grep -q . && break
    p=$(find_window "$PROMPT_RE")
    if [ -n "$p" ] && [ -z "$prompted" ]; then
        prompted=$(cut -f1 <<<"$p")
        shot 03-wine-download-prompt
        kwin activate "$PROMPT_RE" >/dev/null
        sleep 1
        keys esc    # Cancel (there is no network anyway)
    fi
    pgrep -u "$U" -x lucent-bridge >/dev/null || break
    sleep 3
done
if [ -n "$prompted" ]; then
    record wine.no-download-prompt FAIL "Wine asked to download: '$prompted' window $((SECONDS - t_inst)) s after the double-click"
else
    record wine.no-download-prompt PASS "no Wine Mono/Gecko download dialog"
fi
if find_window "$INST_RE" | grep -q .; then
    metric installer_window_after_s $((SECONDS - t_inst))
    record installer.window INFO "installer window $((SECONDS - t_inst)) s after the double-click"
fi
pages=0 focus_note="" step=0
while installer_alive && ((step < 30)); do
    step=$((step + 1))
    w=$(find_window "$INST_RE")
    if [ -z "$w" ]; then sleep 2; continue; fi
    IFS=$'\t' read -r cap _ _ x y ww _ active _ <<<"$w"
    if [ "$active" != 1 ]; then
        click $((x + ww / 2)) $((y + 16))
        sleep 1
        IFS=$'\t' read -r cap _ _ x y ww _ active _ <<<"$(find_window "$INST_RE")"
        if [ "$active" != 1 ]; then
            kwin activate "$INST_RE" >/dev/null
            focus_note="(page $step needed KWin activation: a click on its title bar didn't focus it)"
            sleep 1
        fi
    fi
    shot "03-installer-$(printf %02d "$step")"
    log "installer page $step: $cap"
    keys ret
    pages=$((pages + 1))
    sleep 4
done
t_inst_exit=$SECONDS
if ! installer_alive && ((pages >= 5)); then
    record installer.gui PASS "Notepad++ installer GUI completed with its default buttons: $pages Enter presses, $((t_inst_exit - t_inst)) s $focus_note"
else
    record installer.gui FAIL "installer still running=$(installer_alive && echo yes || echo no) after $pages pages $focus_note"
fi

# Launcher entry for the installed program
APPDIR=$HOMEDIR/.local/share/applications
npp_entry() { grep -lx 'Name=Notepad++' "$APPDIR"/lucent-bridge-*.desktop 2>/dev/null | head -n1; }
APP_RE=' - Notepad\+\+'
if wait_until 90 npp_entry; then
    sleep 1.5
    shot 04-bridge-notification
    record entry.created PASS "$(basename "$(npp_entry)") $((SECONDS - t_inst_exit)) s after the installer closed"
else
    running=$(find_window "$APP_RE" | cut -f1)
    shot 04-no-entry
    record entry.created FAIL "no launcher entry 90 s after the installer closed; Notepad++ started by the installer's Finish page: ${running:-no}. lucent-bridge waits for every process in the prefix (wineserver -w) before it adds entries"
    if [ -n "$running" ]; then
        kwin close "$APP_RE" >/dev/null
        if wait_until 90 npp_entry; then
            record entry.after-close INFO "the entry appeared only after Notepad++ was closed ($(basename "$(npp_entry)"))"
        fi
    fi
fi
# Close what the installer's Finish page started, and let lucent-bridge finish.
if find_window "$APP_RE" | grep -q .; then
    shot 04b-notepadpp-from-installer
    kwin close "$APP_RE" >/dev/null
fi
wait_until 60 bash -c "! pgrep -u $U -f 'notepad\\+\\+\\.exe' >/dev/null"
if wait_until 90 bash -c "! pgrep -u $U -x lucent-bridge >/dev/null"; then
    record bridge.finished INFO "lucent-bridge exited after the prefix emptied"
else
    record bridge.finished FAIL "lucent-bridge still running 90 s after Notepad++ was closed"
fi

entry=$(npp_entry)
if [ -n "$entry" ]; then
    cp "$entry" "$LOGS/"
    wmclass=$(sed -n 's/^StartupWMClass=//p' "$entry")
    icon=$(sed -n 's/^Icon=//p' "$entry")
    exec_line=$(sed -n 's/^Exec=//p' "$entry")
    problems=""
    if command -v desktop-file-validate >/dev/null; then
        desktop-file-validate "$entry" > "$LOGS/entry-validate.txt" 2>&1 || problems+="desktop-file-validate: $(oneline < "$LOGS/entry-validate.txt"); "
    fi
    file "$icon" 2>/dev/null | grep -q 'PNG image' || problems+="icon '$icon' is not a PNG; "
    [[ "$exec_line" == lucent-bridge\ * ]] || problems+="Exec is '$exec_line'; "
    [ -n "$wmclass" ] || problems+="no StartupWMClass; "
    if [ -z "$problems" ]; then
        record entry.valid PASS "Exec=$exec_line; StartupWMClass=$wmclass; icon $(file -b "$icon" | cut -d, -f1-2)"
    else
        record entry.valid FAIL "$problems"
    fi

    # Start it from the launcher: Win key, type, Enter.
    keys meta
    sleep 3
    typetext Notepad++
    sleep 5
    shot 05-launcher-notepadpp-badge
    keys ret
    t_launch=$SECONDS
    app_window() { find_class "$wmclass" | grep -q .; }
    if wait_until 120 app_window; then
        w=$(find_class "$wmclass")
        IFS=$'\t' read -r cap cls wpid _ <<<"$w"
        pid=$wpid
        [ -n "$pid" ] && [ "$pid" != 0 ] && [ -d "/proc/$pid" ] || pid=$(user_pids 'notepad\+\+\.exe' | tail -n1)
        cg=$(cgroup_of "$pid")
        record window.notepadpp PASS "window '$cap' (class $cls, pid $pid) $((SECONDS - t_launch)) s after Enter in the launcher"
        if [[ "$cg" == *'app-lucent\x2dbridge\x2dnotepadplusplus'* ]]; then
            record launch.from-entry PASS "the process runs in its entry's unit: $cg"
        else
            record launch.from-entry FAIL "process $pid is not in the entry's unit: $cg"
        fi
        kwin activate "Notepad\\+\\+" >/dev/null
        sleep 2
        typetext "Hello from Lucent OS - installed by double-click, no network."
        sleep 4
        shot 06-notepadpp-running
        kwin list > "$LOGS/windows.tsv"
    else
        shot 06-no-notepadpp-window
        kwin list > "$LOGS/windows.tsv"
        record window.notepadpp FAIL "no window of class '$wmclass' 120 s after starting it from the launcher"
        record launch.from-entry FAIL "not launched"
    fi
else
    record entry.valid FAIL "no entry"
    record window.notepadpp FAIL "no entry to start it from"
    record launch.from-entry FAIL "no entry"
fi
ls -la "$APPDIR" > "$LOGS/applications.txt" 2>&1
# The app's Wine prefix must carry the labels files in a home get, not the
# template's (/var/lib/lucent-bridge: var_lib_t).
prefix=$(ls -d "$HOMEDIR"/.local/share/lucent-bridge/prefixes/notepadplusplus-* 2>/dev/null | head -n1)
if [ -n "$prefix" ]; then
    # matchpathcon runs in our own domain (restorecon would switch to
    # setfiles_t, which may not write our log files: an AVC of the test's own).
    find "$prefix" -print0 | xargs -0 matchpathcon -V 2>&1 | grep -v ' verified\.$' > "$LOGS/prefix-relabel.txt"
    find "$prefix" -printf '%Z\n' 2>/dev/null | cut -d: -f3 | sort | uniq -c > "$LOGS/prefix-labels.txt"
    n=$(grep -c . "$LOGS/prefix-relabel.txt")
    if ((n == 0)); then
        record prefix.selinux-labels PASS "$prefix: labels as policy expects ($(oneline < "$LOGS/prefix-labels.txt"))"
    else
        record prefix.selinux-labels FAIL "$n files in $prefix carry other labels than policy expects: $(oneline < "$LOGS/prefix-labels.txt"); e.g. $(head -n1 "$LOGS/prefix-relabel.txt")"
    fi
    metric prefix_size "$(du -sh "$prefix" | cut -f1) (apparent; btrfs reflinks share data with the template)"
fi
as_user lucent-bridge list 2>/dev/null | cat > "$LOGS/bridge-list.txt"

# ---------------------------------------------------------------------------
# 6. SELinux, wine-systemd, binfmt
# ---------------------------------------------------------------------------
mode=$(getenforce)
if [ "$mode" = Enforcing ]; then
    record selinux.enforcing PASS "getenforce: Enforcing"
else
    record selinux.enforcing FAIL "getenforce: $mode"
fi
avc_raw=""
if command -v ausearch >/dev/null; then
    avc_src=ausearch
    avc_raw=$(ausearch -m AVC,USER_AVC,SELINUX_ERR,USER_SELINUX_ERR --start boot --format raw 2>/dev/null)
    # "msg=audit(1731150000.123:456)" -> epoch
    avc_flow=$(awk -v s="$flow_start" 'match($0, /audit\([0-9]+/) { if (substr($0, RSTART + 6, RLENGTH - 6) + 0 >= s) print }' <<<"$avc_raw")
else
    avc_src=journal
    avc_raw=$(journalctl -b -o short-unix --no-pager | grep -E 'avc: +denied|SELINUX_ERR')
    avc_flow=$(awk -v s="$flow_start" '$1 + 0 >= s' <<<"$avc_raw")
fi
journalctl -b -o short-unix --no-pager | grep -E 'avc: +denied|SELINUX_ERR' > "$LOGS/avc-journal.txt"
printf '%s\n' "$avc_raw" > "$LOGS/avc-since-boot.txt"
printf '%s\n' "$avc_flow" > "$LOGS/avc-during-flow.txt"
n_all=$(grep -c . <<<"$avc_raw")
n_flow=$(grep -c . <<<"$avc_flow")
metric avc_since_boot "$n_all ($avc_src)"
if ((n_flow == 0)); then
    record selinux.no-avc-flow PASS "no AVC denials from the download to Notepad++ running ($avc_src; $n_all since boot)"
else
    record selinux.no-avc-flow FAIL "$n_flow AVC denials during the flow: $(head -n3 <<<"$avc_flow")"
fi
if rpm -q wine-systemd >/dev/null 2>&1; then
    record wine-systemd.absent FAIL "$(rpm -q wine-systemd)"
else
    record wine-systemd.absent PASS "$(rpm -q wine-systemd 2>&1)"
fi
mz=$(for f in $(grep -l '^magic 4d5a' /proc/sys/fs/binfmt_misc/* 2>/dev/null); do
    printf '%s=%s ' "${f##*/}" "$(sed -n 's/^interpreter //p' "$f")"
done)
if [[ "$mz" =~ ^[A-Za-z]+=/usr/libexec/lucent-bridge/lucent-bridge-binfmt\ $ ]]; then
    record binfmt.mz INFO "the only MZ (.exe) binfmt handler: $mz"
else
    record binfmt.mz FAIL "MZ binfmt handlers: '${mz:-none}'"
fi

failed_units=$(systemctl list-units --failed --plain --no-legend | awk '{print $1}' | tr '\n' ' ')
record system.failed-units INFO "${failed_units:-none}"

log "acceptance test done, failed=$FAILED"
exit 0
