#!/usr/bin/bash
# TEST-ONLY (hardware-live), on the runner, as root: a small office LAN
# for the test VM's igb NIC. A tap device (the "switch port"), a DHCP/DNS
# server and NAT to the internet (the "router"), and an IPP Everywhere
# printer announced over mDNS/DNS-SD (CUPS's ippeveprinter + avahi), as a
# network printer on a home or office network is.
#   lan.sh up USER SPOOL_DIR | lan.sh down
set -uo pipefail
TAP=lucenttap0
case $1 in
up)
    user=$2 spool=$3
    ip tuntap add "$TAP" mode tap user "$user"
    ip addr add 192.168.100.1/24 dev "$TAP"
    ip link set "$TAP" up
    sysctl -qw net.ipv4.ip_forward=1
    iptables -t nat -A POSTROUTING -s 192.168.100.0/24 ! -o "$TAP" -j MASQUERADE
    iptables -I FORWARD 1 -i "$TAP" -j ACCEPT
    iptables -I FORWARD 1 -o "$TAP" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    dnsmasq --conf-file=/dev/null --interface="$TAP" --bind-interfaces --except-interface=lo \
        --dhcp-range=192.168.100.50,192.168.100.99,255.255.255.0,1h \
        --resolv-file=/run/systemd/resolve/resolv.conf --pid-file=/run/lucent-lan-dnsmasq.pid \
        --log-facility=/var/log/lucent-lan-dnsmasq.log --log-dhcp
    sed -i 's/^#\?allow-interfaces=.*/allow-interfaces='"$TAP"'/' /etc/avahi/avahi-daemon.conf
    grep -q "^allow-interfaces=$TAP" /etc/avahi/avahi-daemon.conf ||
        sed -i "/^\[server\]/a allow-interfaces=$TAP" /etc/avahi/avahi-daemon.conf
    systemctl restart avahi-daemon
    mkdir -p "$spool"
    chown "$user" "$spool"
    # -k keeps each job's document; -r _print: IPP Everywhere's DNS-SD subtype.
    sudo -u "$user" setsid -f ippeveprinter -v -k -d "$spool" -p 8631 -r _print \
        -f application/pdf,image/pwg-raster,image/urf,image/jpeg \
        -M Lucent -m "Test Printer" "Lucent Test Printer" > "$spool/../ippeveprinter.log" 2>&1 < /dev/null
    sleep 3
    pgrep -a ippeveprinter
    ;;
down)
    pkill ippeveprinter
    [ -f /run/lucent-lan-dnsmasq.pid ] && kill "$(cat /run/lucent-lan-dnsmasq.pid)"
    ip link del "$TAP" 2> /dev/null
    ;;
esac
exit 0
