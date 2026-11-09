#!/usr/bin/bash
# TEST-ONLY (hardware-live), as root: pair the computer's Bluetooth adapter
# (first virtual controller) with the second virtual controller acting as
# a device nearby. Both come from btvirt -l2 (BlueZ's emulator over
# hci_vhci); its controllers find each other in inquiry and page.
#   bt-pair.sh ADAPTER_ADDR DEVICE_ADDR
set -uo pipefail
a=$1 d=$2
{
    echo "select $d"
    echo "system-alias Lucent Test Headphones"
    echo "power on"
    echo "pairable on"
    echo "discoverable on"
    echo "agent NoInputNoOutput"
    echo "default-agent"
    echo "select $a"
    echo "power on"
    echo "scan on"
    sleep 15
    echo "scan off"
    echo "devices"
    echo "pair $d"
    sleep 15
    echo "trust $d"
    echo "info $d"
    sleep 2
    echo "quit"
} | bluetoothctl
