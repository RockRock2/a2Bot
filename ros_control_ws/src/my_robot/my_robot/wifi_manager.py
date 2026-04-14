#!/usr/bin/env python3
"""
WiFi provisioning helper for EduBot.
Uses nmcli (NetworkManager CLI) to manage WiFi connections and hotspot.
"""
import subprocess
import time

HOTSPOT_CON = "EduBot-AP"
HOTSPOT_SSID = "EduBot-Setup"
HOTSPOT_IP = "192.168.4.1"
IFACE = "wlan0"


def _nmcli_available() -> bool:
    import shutil
    return shutil.which("nmcli") is not None


def _run(cmd, timeout=10):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def get_status() -> dict:
    """Return current WiFi status as {mode, ssid, ip, signal}."""
    if not _nmcli_available():
        # NetworkManager not installed — report connected with best-effort IP
        return {"mode": "connected", "ssid": "unknown", "ip": _get_ip(), "signal": 0}
    try:
        r = _run(["nmcli", "-t", "-f", "STATE,CONNECTIVITY", "general"])
        line = r.stdout.strip().split("\n")[0]
        parts = line.split(":")
        state = parts[0] if parts else ""
        connectivity = parts[1] if len(parts) > 1 else ""

        if state == "connected" and connectivity == "full":
            ssid_r = _run(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi"])
            for row in ssid_r.stdout.strip().splitlines():
                cols = row.split(":")
                if len(cols) >= 3 and cols[0] == "yes":
                    ssid = cols[1]
                    signal = int(cols[2]) if cols[2].isdigit() else 0
                    dbm = round(-100 + signal * 0.7)
                    return {"mode": "connected", "ssid": ssid,
                            "ip": _get_ip(), "signal": dbm}

        # Check if our hotspot is active
        r2 = _run(["nmcli", "-t", "-f", "NAME,STATE", "con", "show", "--active"])
        for row in r2.stdout.strip().splitlines():
            if HOTSPOT_CON in row and "activated" in row:
                return {"mode": "hotspot", "ssid": HOTSPOT_SSID,
                        "ip": HOTSPOT_IP, "signal": 0}
    except Exception:
        pass
    return {"mode": "disconnected", "ssid": "", "ip": "", "signal": 0}


def scan_networks() -> list:
    """Return list of visible WiFi networks sorted by signal strength."""
    try:
        _run(["nmcli", "dev", "wifi", "rescan"])
        time.sleep(2)
        r = _run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi"], timeout=15)
        seen, networks = set(), []
        for row in r.stdout.strip().splitlines():
            cols = row.split(":")
            if len(cols) < 2:
                continue
            ssid, signal = cols[0], cols[1]
            if ssid and ssid not in seen:
                seen.add(ssid)
                networks.append({"ssid": ssid,
                                 "signal": int(signal) if signal.isdigit() else 0})
        networks.sort(key=lambda x: -x["signal"])
        return networks
    except Exception:
        return []


def connect(ssid: str, password: str) -> dict:
    """Connect to a WiFi network. Returns {ok, ip, error}."""
    try:
        cmd = ["nmcli", "dev", "wifi", "connect", ssid]
        if password:
            cmd += ["password", password]
        cmd += ["ifname", IFACE]
        r = _run(cmd, timeout=30)
        if r.returncode == 0:
            time.sleep(3)  # allow DHCP lease
            ip = _get_ip()
            _run(["nmcli", "con", "delete", HOTSPOT_CON])  # tear down hotspot
            return {"ok": True, "ip": ip}
        return {"ok": False, "error": r.stderr.strip() or r.stdout.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ensure_connectivity():
    """Called at startup: if no WiFi, start hotspot for provisioning."""
    if not _nmcli_available():
        return  # WiFi provisioning requires NetworkManager — skip silently
    status = get_status()
    if status["mode"] == "connected":
        return
    _start_hotspot()


def _start_hotspot():
    """Create and activate a WiFi AP via NetworkManager."""
    _run(["nmcli", "con", "delete", HOTSPOT_CON])  # clean up any prior entry
    _run([
        "nmcli", "con", "add",
        "type", "wifi", "ifname", IFACE,
        "con-name", HOTSPOT_CON,
        "ssid", HOTSPOT_SSID,
        "mode", "ap",
        "ipv4.method", "shared",
        "ipv4.addresses", f"{HOTSPOT_IP}/24",
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", "edubot123",
    ])
    _run(["nmcli", "con", "up", HOTSPOT_CON])


def _get_ip() -> str:
    """Return the IPv4 address of wlan0."""
    try:
        r = _run(["ip", "-4", "addr", "show", IFACE])
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                return line.split()[1].split("/")[0]
    except Exception:
        pass
    return ""
