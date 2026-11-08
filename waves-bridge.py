#!/usr/bin/env python3
"""
waves-bridge.py - make Waves plugins load bridged from FL Studio's browser under Wine.

Copies the 25-byte wrapper-settings record (event 213, record id 2) from a
donor .fst you bridged by hand onto every plugin-database entry you point it at.

See docs/fst-format.md for the format.

Usage:
    python3 waves-bridge.py <donor.fst> <target.fst> [target.fst ...]
    python3 waves-bridge.py --dry-run <donor.fst> <target.fst> ...

Typical:
    DB="$WINEPREFIX/drive_c/users/$USER/Documents/Image-Line/FL Studio/Presets/Plugin database/Installed/Effects"
    mapfile -d '' W < <(grep -rlZa 'WaveShell' "$DB" --include='*.fst')
    python3 waves-bridge.py "/path/to/MyPlugin BRIDGED.fst" "${W[@]}"

Back up first. .fst files are small:
    cd "$HOME" && find . -path '*Plugin database*' -name '*.fst' \
      | tar -czf ~/fl-fst-backup.tar.gz -T -
"""

import sys
import struct

WRAPPER_EVENT = 213
SETTINGS_RECORD = 2


def wrapper_payload(d):
    """Return (offset, length) of event 213's data, or (None, None)."""
    if d[0:4] != b"FLhd":
        return None, None
    pos = 8 + struct.unpack_from("<I", d, 4)[0]
    if d[pos:pos + 4] != b"FLdt":
        return None, None
    end = pos + 8 + struct.unpack_from("<I", d, pos + 4)[0]
    pos += 8
    while pos < end:
        ev = d[pos]
        pos += 1
        if ev < 64:
            pos += 1
        elif ev < 128:
            pos += 2
        elif ev < 192:
            pos += 4
        else:
            n = shift = 0
            while True:
                b = d[pos]
                pos += 1
                n |= (b & 0x7F) << shift
                shift += 7
                if not b & 0x80:
                    break
            if ev == WRAPPER_EVENT:
                return pos, n
            pos += n
    return None, None


def settings_record(d, offset, length):
    """Find record id 2 inside the wrapper payload. Returns (offset, length)."""
    end = offset + length
    p = offset
    while p + 12 <= end:
        fid = struct.unpack_from("<I", d, p)[0]
        ln = struct.unpack_from("<Q", d, p + 4)[0]
        if 0 < fid < 4096 and 0 < ln <= end - (p + 12):
            if fid == SETTINGS_RECORD:
                return p + 12, ln
            p += 12 + ln
        else:
            p += 1          # resync: the payload has a fixed header before the records
    return None, None


def read_settings(path):
    d = open(path, "rb").read()
    o, n = wrapper_payload(d)
    if o is None:
        return None, None, None
    p, l = settings_record(d, o, n)
    if p is None:
        return None, None, None
    return d, p, l


def main(argv):
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    if len(argv) < 3:
        print(__doc__.strip())
        return 1

    donor = argv[1]
    src, sp, sl = read_settings(donor)
    if src is None:
        print(f"error: no wrapper settings record in donor {donor}")
        return 1
    record = src[sp:sp + sl]
    print(f"donor  : {donor}")
    print(f"record : {record.hex(' ')}  ({sl} bytes)")
    if record[0] == 0:
        print("warning: donor's settings-valid marker (byte 0) is clear.")
        print("         Bridge and detach the plugin by hand, re-save the preset, try again.")
    print()

    patched = skipped = 0
    for target in argv[2:]:
        try:
            d = bytearray(open(target, "rb").read())
        except OSError as e:
            print(f"skip  {target}: {e}")
            skipped += 1
            continue
        o, n = wrapper_payload(d)
        if o is None:
            print(f"skip  {target}: not an FL plugin state file")
            skipped += 1
            continue
        p, l = settings_record(d, o, n)
        if p is None:
            print(f"skip  {target}: no settings record")
            skipped += 1
            continue
        if l != sl:
            print(f"skip  {target}: record is {l} bytes, donor is {sl}")
            skipped += 1
            continue
        if bytes(d[p:p + l]) == record:
            skipped += 1
            continue
        if not dry:
            d[p:p + l] = record
            open(target, "wb").write(d)
        patched += 1

    verb = "would patch" if dry else "patched"
    print(f"{verb} {patched}, skipped or already done {skipped}")
    if patched and not dry:
        print("Restart FL Studio - it caches the plugin database at startup.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
