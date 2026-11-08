#!/usr/bin/env python3
"""
fst-inspect.py - look inside FL Studio .fst files.

    fst-inspect.py events  <file...>          list the event stream
    fst-inspect.py records <file...>          list event-213 records
    fst-inspect.py flags   <file...>          show the wrapper settings record
    fst-inspect.py diff    <a.fst> <b.fst>    byte diff, in event-213 coordinates

`diff` is the one that found everything: save a plugin twice with one checkbox
changed, diff the two files, and the flag bits are whatever moved.

See ../docs/fst-format.md.
"""

import sys
import struct

WRAPPER_EVENT = 213


def payload(d):
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


def cmd_events(paths):
    for path in paths:
        d = open(path, "rb").read()
        print(f"\n=== {path}  ({len(d)} bytes)")
        if d[0:4] != b"FLhd":
            print("  not an FL state file")
            continue
        pos = 8 + struct.unpack_from("<I", d, 4)[0]
        end = pos + 8 + struct.unpack_from("<I", d, pos + 4)[0]
        pos += 8
        while pos < end:
            ev = d[pos]
            pos += 1
            if ev < 64:
                n, dat = 1, pos
            elif ev < 128:
                n, dat = 2, pos
            elif ev < 192:
                n, dat = 4, pos
            else:
                n = shift = 0
                while True:
                    b = d[pos]
                    pos += 1
                    n |= (b & 0x7F) << shift
                    shift += 7
                    if not b & 0x80:
                        break
                dat = pos
            tag = "   <- plugin wrapper" if ev == WRAPPER_EVENT else ""
            print(f"  ev {ev:3d}  data {dat:6d}..{dat+n-1:<6d} len {n:<7d}{tag}")
            pos = dat + n


def cmd_records(paths):
    for path in paths:
        d = open(path, "rb").read()
        o, n = payload(d)
        print(f"\n=== {path}   event 213 @ {o}, len {n}")
        if o is None:
            print("  no wrapper event")
            continue
        end, p = o + n, o
        while p + 12 <= end:
            fid = struct.unpack_from("<I", d, p)[0]
            ln = struct.unpack_from("<Q", d, p + 4)[0]
            if 0 < fid < 4096 and 0 < ln <= end - (p + 12):
                txt = "".join(chr(c) if 32 <= c < 127 else "." for c in d[p + 12:p + 12 + min(ln, 56)])
                print(f"  +{p-o:<6} id {fid:<5} len {ln:<8} {txt}")
                p += 12 + ln
            else:
                p += 1


def cmd_flags(paths):
    for path in paths:
        d = open(path, "rb").read()
        o, n = payload(d)
        if o is None:
            print(f"{path}: no wrapper event")
            continue
        end, p, rec = o + n, o, None
        while p + 12 <= end:
            fid = struct.unpack_from("<I", d, p)[0]
            ln = struct.unpack_from("<Q", d, p + 4)[0]
            if 0 < fid < 4096 and 0 < ln <= end - (p + 12):
                if fid == 2:
                    rec = d[p + 12:p + 12 + ln]
                    break
                p += 12 + ln
            else:
                p += 1
        if rec is None:
            print(f"{path}: no settings record")
            continue
        w = struct.unpack_from("<i", rec, 1)[0]
        h = struct.unpack_from("<i", rec, 5)[0]
        print(f"\n=== {path}")
        print(f"  record   {rec.hex(' ')}")
        print(f"  marker   {'set' if rec[0] else 'CLEAR  (FL will ignore the window flag)'}")
        print(f"  editor   {w} x {h}" + ("   (unset)" if w < 0 else ""))
        print(f"  bridged  {'yes' if rec[10] & 0x02 else 'no'}")
        print(f"  external {'yes' if rec[11] & 0x20 else 'no'}")


def cmd_diff(a_path, b_path):
    a = open(a_path, "rb").read()
    b = open(b_path, "rb").read()
    oa, _ = payload(a)
    print(f"A = {a_path}   {len(a)} B   event 213 @ {oa}")
    print(f"B = {b_path}   {len(b)} B\n")
    n = 0
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            rel = f"ev213 +{i-oa}" if oa is not None else ""
            print(f"  abs {i:<7} {rel:<14} {a[i]:#04x} -> {b[i]:#04x}")
            n += 1
    extra = "" if len(a) == len(b) else f"   (sizes differ: {len(a)} vs {len(b)})"
    print(f"\n{n} differing bytes{extra}")


def main(argv):
    if len(argv) < 3:
        print(__doc__.strip())
        return 1
    cmd, args = argv[1], argv[2:]
    if cmd == "events":
        cmd_events(args)
    elif cmd == "records":
        cmd_records(args)
    elif cmd == "flags":
        cmd_flags(args)
    elif cmd == "diff":
        if len(args) != 2:
            print("diff takes exactly two files")
            return 1
        cmd_diff(*args)
    else:
        print(__doc__.strip())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
