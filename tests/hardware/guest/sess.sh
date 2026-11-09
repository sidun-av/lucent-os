#!/usr/bin/bash
# TEST-ONLY (hardware-live). Run the script on stdin inside the Plasma
# session of the calling user: through the session's systemd --user
# manager, the way KRunner and Dolphin start programs. So udisks/polkit see
# the active local session (not this SSH login), and the program gets the
# session's WAYLAND_DISPLAY and D-Bus. Prints its output, exits with its code.
#   ssh lucent@vm bash /var/tmp/hwtest/sess.sh < script
d=$(mktemp -d /var/tmp/hwtest/sess.XXXXXX)
cat > "$d/s.sh"
systemd-run --user --quiet --wait --collect -p RuntimeMaxSec="${SESS_MAX:-300}" \
    -- /usr/bin/bash -c "/usr/bin/bash '$d/s.sh' > '$d/out' 2>&1; echo \$? > '$d/rc'" > /dev/null 2>&1
cat "$d/out" 2> /dev/null
rc=$(cat "$d/rc" 2> /dev/null || echo 125)
rm -rf "$d"
exit "$rc"
