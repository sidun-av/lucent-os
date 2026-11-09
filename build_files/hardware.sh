#!/usr/bin/bash
# Lucent OS: hardware that works right after installation, like on Windows.
# Called once by build.sh; build context at /ctx. docs/hardware.md explains
# it for users; tests/hardware/hw_audit.py checks the result in CI
# (.github/workflows/hardware-audit.yml).
#
# Fedora Kinoite already carries most drivers and firmware (kernel-modules,
# kernel-modules-extra, the linux-firmware set, PipeWire, BlueZ, CUPS, SANE,
# Mesa). build_files/hardware-packages.txt is the full list Lucent relies
# on; whatever the base image lacks is installed here, and the build log
# shows what each added package costs.
set -xeuo pipefail
ARCH=$(uname -m)
DNF=$(command -v dnf5 || command -v dnf)
# No weak dependencies, as in build.sh: only what is listed, plus what it
# strictly needs.
DNF_OPTS=(-y --setopt=install_weak_deps=False --setopt=clean_requirements_on_remove=False)
LIST=/ctx/build_files/hardware-packages.txt

mapfile -t WANT < <(awk -v a="$ARCH" '!/^[[:space:]]*#/ && NF >= 3 && ($2 == "any" || $2 == a) {print $1}' "$LIST")
((${#WANT[@]} > 20)) || { echo "hardware-packages.txt: suspiciously short (${#WANT[@]} packages)"; exit 1; }

rpm -qa --qf '%{NAME}\t%{SIZE}\n' | LC_ALL=C sort > /tmp/hw-before.tsv
missing=()
for p in "${WANT[@]}"; do rpm -q "$p" &>/dev/null || missing+=("$p"); done
if ((${#missing[@]})); then
    echo "== Hardware support the base image lacks: ${missing[*]}"
    "$DNF" "${DNF_OPTS[@]}" install "${missing[@]}"
fi

# Every listed package must now be there (a renamed or dropped Fedora
# package fails the build here rather than a user's laptop later).
for p in "${WANT[@]}"; do rpm -q "$p" >/dev/null; done

# What it cost: every package that is new in the image (listed ones and
# their dependencies), largest first.
rpm -qa --qf '%{NAME}\t%{SIZE}\n' | LC_ALL=C sort > /tmp/hw-after.tsv
echo "== Added by hardware.sh (installed size)"
LC_ALL=C join -t $'\t' -v 2 /tmp/hw-before.tsv /tmp/hw-after.tsv \
    | sort -t $'\t' -k2,2nr \
    | awk -F '\t' '{printf "%8.1f MB  %s\n", $2 / 1e6, $1; t += $2} END {printf "%8.1f MB  total\n", t / 1e6}'
rm -f /tmp/hw-before.tsv /tmp/hw-after.tsv

# ---------------------------------------------------------------------------
# Services. Boot-time services are boot-perf's (build_files/performance.sh);
# only hardware daemons are touched here, each with a reason.
# ---------------------------------------------------------------------------
if [ "$ARCH" = x86_64 ]; then
    # thermald: Intel's thermal daemon keeps Intel laptops from overheating
    # and throttling hard under load, using the limits the laptop maker put
    # in the firmware (DPTF/ACPI tables). Windows does the same through
    # Intel's DPTF driver. It is useless on AMD CPUs and in virtual
    # machines, so there it is skipped cleanly (ExecCondition, not a failed
    # unit) instead of starting and exiting.
    mkdir -p /usr/lib/systemd/system/thermald.service.d
    cat > /usr/lib/systemd/system/thermald.service.d/50-lucent-intel-only.conf <<'EOF'
# Lucent OS (build_files/hardware.sh): Intel thermal daemon only on Intel
# CPUs, and never in a virtual machine.
[Unit]
ConditionVirtualization=no

[Service]
ExecCondition=/usr/bin/grep -q -m1 GenuineIntel /proc/cpuinfo
EOF
    systemctl enable thermald.service
fi
