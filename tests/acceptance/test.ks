# Lucent OS acceptance test: kickstart for an unattended install. TEST-ONLY.
#
# Put on a throw-away copy of the release ISO by .github/workflows/acceptance.yml
# (mkksiso --ks); the release ISO and images never contain any of it. It adds
# what an unattended run needs, a user ("anna"), and, in %post, autologin and
# the test runner service, then includes the ISO's own kickstart (which
# carries iso/lucent-apps.ks: the offline apps).
%include /run/install/repo/osbuild.ks
text --non-interactive
lang en_US.UTF-8
keyboard us
timezone UTC --utc
ignoredisk --only-use=vda
zerombr
clearpart --all --initlabel --disklabel=gpt
# Fedora Atomic's default layout (btrfs), as an interactive install makes it.
autopart --noswap --type=btrfs
rootpw --lock
user --name=anna --gecos="Anna" --groups=wheel --password=lucent-acceptance --plaintext
poweroff

%post --nochroot --interpreter=/usr/bin/bash --log=/tmp/lucent-acceptance-post.log
# TEST-ONLY: autologin and the acceptance runner on the installed system.
set -x
if [ -c /dev/ttyS0 ]; then exec > >(tee -a /dev/ttyS0) 2>&1; fi
root=/mnt/sysroot
mkdir -p "$root/etc/plasmalogin.conf.d" "$root/etc/lucent-acceptance"
cat > "$root/etc/plasmalogin.conf.d/zz-lucent-acceptance-autologin.conf" <<'EOF'
# TEST-ONLY (acceptance test install). Never part of a release.
[Autologin]
User=anna
Session=plasma.desktop
Relogin=false
EOF
# Waits for the payload disk the CI harness attaches and runs the test from it.
cat > "$root/etc/lucent-acceptance/start.sh" <<'EOF'
#!/usr/bin/bash
# TEST-ONLY: run the acceptance test from the payload disk, if there is one.
for _ in $(seq 120); do
    [ -e /dev/disk/by-label/LUCENTTEST ] && [ -e /dev/virtio-ports/org.lucent.acceptance ] && break
    sleep 1
done
[ -e /dev/disk/by-label/LUCENTTEST ] || exit 0
mkdir -p /run/lucent-acceptance
mount -o context=system_u:object_r:var_lib_t:s0 /dev/disk/by-label/LUCENTTEST /run/lucent-acceptance
exec /usr/bin/bash /run/lucent-acceptance/guest/acceptance.sh /run/lucent-acceptance
EOF
cat > "$root/etc/systemd/system/lucent-acceptance.service" <<'EOF'
# TEST-ONLY (acceptance test install). Never part of a release.
[Unit]
Description=Lucent OS acceptance test (CI)
After=local-fs.target systemd-user-sessions.service

[Service]
Type=simple
ExecStart=/usr/bin/bash /etc/lucent-acceptance/start.sh
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF
chroot "$root" systemctl enable lucent-acceptance.service
# SELinux labels from the new system's own policy (as iso/lucent-apps.ks does).
chroot "$root" /usr/bin/bash -c '
    policy=$(sed -n "s/^SELINUXTYPE=//p" /etc/selinux/config)
    sel=/etc/selinux/${policy:-targeted}
    bin=$(ls "$sel"/policy/policy.* 2>/dev/null | sort -V | tail -n1)
    setfiles -F -c "$bin" "$sel/contexts/files/file_contexts" \
        /etc/plasmalogin.conf.d /etc/lucent-acceptance /etc/systemd/system ||
        echo "setfiles failed"
    ls -lZ /etc/plasmalogin.conf.d /etc/lucent-acceptance /etc/systemd/system/lucent-acceptance.service'
echo "lucent-acceptance: test setup done"
%end
