#!/usr/bin/bash
# TEST-ONLY (hardware-live), as root in the test VM: a virtual Wi-Fi router.
#
# mac80211_hwsim makes two Wi-Fi radios that hear each other over a
# simulated medium. The second one, together with the rig's uplink NIC
# (MAC 52:54:00:4c:00:02, unmanaged by NetworkManager), goes into a network
# namespace of its own, "apns", where hostapd runs a WPA2-PSK network,
# dnsmasq hands out addresses and DNS, and nftables NATs to the uplink. The
# computer keeps only the first radio, as a laptop would: NetworkManager
# and the taskbar see one Wi-Fi card and one network to join.
#   wifi-ap.sh SSID PASSPHRASE
set -euo pipefail
ssid=$1 psk=$2
T=/var/tmp/hwtest
modprobe mac80211_hwsim radios=2
for _ in $(seq 20); do
    mapfile -t phys < <(for p in /sys/class/ieee80211/*; do
        [ "$(basename "$(readlink -f "$p/device/driver")")" = mac80211_hwsim ] && basename "$p"
    done | sort -V)
    ((${#phys[@]} >= 2)) && break
    sleep 1
done
((${#phys[@]} >= 2)) || { echo "hwsim radios: ${phys[*]:-none}"; exit 1; }
ap_phy=${phys[1]}
ap_if=$(ls "/sys/class/ieee80211/$ap_phy/device/net/" | head -n1)
wan_if=""
for i in /sys/class/net/*; do
    [ "$(cat "$i/address")" = 52:54:00:4c:00:02 ] && wan_if=${i##*/}
done
[ -n "$wan_if" ] || { echo "no uplink NIC"; exit 1; }
echo "client radio: ${phys[0]}; access point: $ap_phy ($ap_if), uplink $wan_if"
nmcli device set "$ap_if" managed no || true
ip netns add apns
iw phy "$ap_phy" set netns name apns
ip link set dev "$wan_if" netns apns
N="ip netns exec apns"
$N ip link set lo up
$N ip link set "$wan_if" name wan
$N ip addr add 10.0.2.15/24 dev wan
$N ip link set wan up
$N ip route add default via 10.0.2.2
$N ip addr add 192.168.77.1/24 dev "$ap_if"
$N ip link set "$ap_if" up
$N sysctl -qw net.ipv4.ip_forward=1
$N nft -f - <<'EOF'
table ip hwtest {
    chain post { type nat hook postrouting priority 100; oifname "wan" masquerade; }
}
EOF
cat > "$T/hostapd.conf" <<EOF
interface=$ap_if
driver=nl80211
ssid=$ssid
country_code=US
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=$psk
ctrl_interface=/run/hwtest-hostapd
EOF
# Binaries copied to /var/tmp run unconfined (test rig, not the system).
$N "$T/bin/hostapd" -B -P /run/hwtest-hostapd.pid -f "$T/hostapd.log" -t "$T/hostapd.conf"
$N "$T/bin/dnsmasq" --conf-file=/dev/null --interface="$ap_if" --bind-interfaces --except-interface=lo \
    --dhcp-range=192.168.77.50,192.168.77.150,255.255.255.0,1h --dhcp-option=3,192.168.77.1 \
    --dhcp-option=6,192.168.77.1 --server=10.0.2.3 --no-resolv --no-hosts --user=root --group=root \
    --pid-file=/run/hwtest-dnsmasq.pid --log-facility="$T/dnsmasq.log" --log-dhcp
sleep 2
$N iw dev
$N ping -c1 -W3 10.0.2.2 > /dev/null && echo "access point uplink: ok" || echo "access point uplink: no answer from 10.0.2.2 (QEMU user network may not answer ping)"
