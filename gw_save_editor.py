#!/usr/bin/env python3
import os
import sys
import json
import shutil
import hashlib
import platform

APP_ID = "com.groundwork-simulator.groundwork-simulator"
MARKER = b"groundwork-simulator-campaign-v1"


def get_default_saves_dir():
    system = platform.system()
    candidates = []

    if system == "Darwin":  # macOS
        candidates.append(
            os.path.expanduser(f"~/Library/Application Support/{APP_ID}/saves/slots")
        )
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if appdata:
            candidates.append(os.path.join(appdata, APP_ID, "saves", "slots"))
        if localappdata:
            candidates.append(os.path.join(localappdata, APP_ID, "saves", "slots"))
    else:  # Linux / Steam Deck
        candidates.append(
            os.path.expanduser(f"~/.local/share/{APP_ID}/saves/slots")
        )

    # Also check current directory as a fallback
    candidates.append(os.getcwd())

    for path in candidates:
        if os.path.isdir(path):
            slots = [f for f in os.listdir(path) if f.endswith(".groundwork-simulator")]
            if slots:
                return path
    return None


def load_save(slot_path):
    with open(slot_path, "rb") as f:
        data = f.read()

    gw_pos = data.rfind(b"GWCOMMIT")
    if gw_pos == -1:
        raise ValueError("Could not find GWCOMMIT footer in save file.")

    header32 = data[gw_pos : gw_pos + 32]
    offset = int.from_bytes(header32[8:16], "little")
    length = int.from_bytes(header32[16:24], "little")
    count = int.from_bytes(header32[24:32], "little")
    snap = data[offset : offset + length]

    m_idx = snap.find(MARKER)
    if m_idx == -1:
        raise ValueError("Could not find campaign data inside the active snapshot.")

    arr_start = m_idx + len(MARKER)
    if snap[arr_start] != 0xDC:
        raise ValueError(f"Unexpected MessagePack array header: {hex(snap[arr_start])}")

    json_len = int.from_bytes(snap[arr_start + 1 : arr_start + 3], "big")
    json_start = arr_start + 3
    json_end = json_start + json_len
    camp = json.loads(snap[json_start:json_end].decode("utf-8"))

    return data, offset, count, snap, arr_start, json_end, camp


def save_changes(slot_path, data, offset, count, snap, arr_start, json_end, camp):
    # Create safety backup first
    shutil.copy2(slot_path, slot_path + ".bak")

    new_json = json.dumps(camp, separators=(",", ":")).encode("utf-8")
    new_len_bytes = len(new_json).to_bytes(2, "big")
    new_snap = snap[: arr_start + 1] + new_len_bytes + new_json + snap[json_end:]

    # Rebuild 96-byte GWCOMMIT footer with valid double SHA-256 digest
    new_header32 = (
        b"GWCOMMIT"
        + offset.to_bytes(8, "little")
        + len(new_snap).to_bytes(8, "little")
        + count.to_bytes(8, "little")
    )
    h1 = hashlib.sha256(new_snap).digest()
    h2 = hashlib.sha256(new_header32 + h1).digest()
    new_footer = new_header32 + h1 + h2

    with open(slot_path, "wb") as f:
        f.write(data[:offset] + new_snap + new_footer)


def calc_live_balance(funds):
    opening = funds.get("opening_balance_eur", 0)
    ledger_sum = sum(
        item.get("amount_eur", 0) for item in funds.get("ledger_postings", [])
    )
    gold_rev = funds.get("applied_gold_proceeds_eur", 0)
    return opening + ledger_sum + gold_rev


def resolve_slot_path():
    # Allow passing a file or folder path directly via CLI argument
    if len(sys.argv) > 1:
        arg = os.path.expanduser(sys.argv[1].strip("\"'"))
        if os.path.isfile(arg):
            return arg
        if os.path.isdir(arg):
            saves_dir = arg
        else:
            print(f"Path not found: {arg}")
            sys.exit(1)
    else:
        saves_dir = get_default_saves_dir()

    if not saves_dir:
        manual = input(
            "Default save folder not found.\nPaste path to your save file or 'slots' folder: "
        ).strip().strip("\"'")
        manual = os.path.expanduser(manual)
        if os.path.isfile(manual):
            return manual
        if os.path.isdir(manual):
            saves_dir = manual
        else:
            print("Invalid path.")
            sys.exit(1)

    slots = sorted(
        f for f in os.listdir(saves_dir) if f.endswith(".groundwork-simulator")
    )
    if not slots:
        print(f"No .groundwork-simulator files found in: {saves_dir}")
        sys.exit(1)

    print(f"Save directory: {saves_dir}\n")
    for i, name in enumerate(slots, 1):
        print(f"  [{i}] {name}")

    choice = input(f"\nSelect save slot (1-{len(slots)}, default 1): ").strip()
    idx = int(choice) - 1 if choice else 0
    if not (0 <= idx < len(slots)):
        print("Invalid slot selection.")
        sys.exit(1)

    return os.path.join(saves_dir, slots[idx])


def main():
    print(f"=== Groundwork Simulator Save Editor ({platform.system()}) ===")
    slot_path = resolve_slot_path()

    data, offset, count, snap, arr_start, json_end, camp = load_save(slot_path)
    funds = camp["funds"]

    print(f"\nLoaded: {os.path.basename(slot_path)}")
    print(f"  Opening Balance : {funds.get('opening_balance_eur', 0):,} EUR")
    print(f"  Live Cash       : {calc_live_balance(funds):,} EUR")
    print(f"  Gold Held       : {funds.get('gold', {}).get('grams', 0)} g")
    print(f"  Active Loans    : {len(funds.get('loans', []))}")

    print("\nWhat would you like to edit?")
    print("  [1] Set Cash / Opening Balance (EUR)")
    print("  [2] Set Gold Weight (grams)")
    print("  [3] Clear All Loans")
    action = input("Choose option (1-3): ").strip()

    if action == "1":
        raw_val = input("Enter desired live cash balance (EUR): ").strip().replace(",", "")
        target_cash = int(raw_val)
        ledger_sum = sum(
            item.get("amount_eur", 0) for item in funds.get("ledger_postings", [])
        )
        gold_rev = funds.get("applied_gold_proceeds_eur", 0)
        funds["opening_balance_eur"] = target_cash - ledger_sum - gold_rev
        print(
            f"Set opening_balance_eur to {funds['opening_balance_eur']:,} EUR "
            f"(live cash will be {target_cash:,} EUR)."
        )
    elif action == "2":
        grams = float(input("Enter desired gold weight in grams: ").strip())
        funds.setdefault("gold", {})["grams"] = grams
        print(f"Set gold weight to {grams} g.")
    elif action == "3":
        funds["loans"] = []
        print("Cleared all active loans.")
    else:
        print("No changes made.")
        sys.exit(0)

    save_changes(slot_path, data, offset, count, snap, arr_start, json_end, camp)
    print(f"\nSaved cleanly! Backup created at:\n  {slot_path}.bak")


if __name__ == "__main__":
    main()
