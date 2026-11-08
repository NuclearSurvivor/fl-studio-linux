# The `.fst` format, and where the wrapper settings live

Reverse-engineered against FL Studio 2025 v25.2.3 build 5171. Everything below was
confirmed by A/B — save the same plugin twice with one checkbox changed, diff the
bytes — across four plugins (CLA-2A, CLA-76, H-Delay, Waves Tune Real-Time) and
then validated by writing the bytes back and checking FL's UI.

## Container

An `.fst` is an FLP event stream.

```
"FLhd"  uint32 len   <header bytes>
"FLdt"  uint32 len   <event stream>
```

Events are `id (uint8)` plus a payload whose size depends on the id:

| id range | payload |
|---|---|
| 0–63 | 1 byte |
| 64–127 | 2 bytes |
| 128–191 | 4 bytes |
| 192–255 | varint length, then that many bytes |

Varints are little-endian 7-bit groups with the high bit as continuation.

**Event `213` is the plugin wrapper.** That's the one that matters.

## Inside event 213

The payload opens with a fixed header, then a list of records:

```
uint32  record id
uint64  record length
bytes   record data
```

Records seen in Waves entries:

| id | length | contents |
|---|---|---|
| 1 | 20 | (presets only) |
| 2 | **25** | **wrapper settings — bridging, external window, editor geometry** |
| 30 / 31 / 32 | 16 / 12 / 12 | (presets only) |
| 50 | 16 | |
| 52 | 16 | VST3 class ID, e.g. `MTSVDOmMondomod ` |
| 53 | varies | plugin state blob (presets only) |
| 54 | 24 | `WaveShell1-VST3 16.7_x64` |
| 55 | 64 | `C:\Program Files\Common Files\VST3\WaveShell1-VST3 16.7_x64.vst3` |
| 56 | 5 | `Waves` |

A scan stub (what FL writes into the plugin database when it scans) carries only
records 2, 50, 52, 54, 55, 56 and runs about 378 bytes. A saved preset adds
records 1, 30, 31, 32 and the state blob, so it's much larger and the records sit
at different absolute offsets. **Parse for the record id — don't seek to a fixed
offset.** The parser in [`waves-bridge.py`](../waves-bridge.py) resyncs byte by
byte when a candidate header fails its sanity check, which handles both shapes
with one code path.

## Record `id 2` — wrapper settings

25 bytes:

| offset | size | meaning |
|---|---|---|
| 0 | 1 | settings-valid marker |
| 1 | 4 | editor width, int32 LE |
| 5 | 4 | editor height, int32 LE |
| 9 | 1 | |
| 10 | 1 | bit `0x02` — **Make bridged** |
| 11 | 1 | bit `0x04` — Make bridged (companion) · bit `0x20` — **External window** |
| 12 | 1 | |
| 13–24 | 12 | |

A plugin bridged and detached by hand:

```
01 31 02 00 00 9a 01 00 00 8c 7f 24 b4 00 00 00 00 01 00 00 00 00 00 00 00
^^ ^^^^^^^^^^^ ^^^^^^^^^^^    ^^ ^^
|  width 561   height 410     |  0x04 | 0x20
marker                        0x02
```

The same plugin as FL's scanner writes it:

```
00 ff ff ff ff ff ff ff ff 08 7d 50 00 00 00 00 00 01 00 00 00 00 00 00 00
^^ ^^^^^^^^^^^^^^^^^^^^^^^
|  width/height = -1 / -1
marker clear
```

## Why you copy the record instead of setting the bits

Setting bit `0x02` at offset 10 works — the plugin comes up bridged. Setting bit
`0x20` at offset 11 does **not** work on a scan stub, no matter how correctly you
set it.

FL won't apply a window flag when the settings-valid marker is clear and the
editor rectangle is `-1 / -1`. There's no window to place, so the flag is
discarded. Bridging needs no rectangle, which is why exactly half the patch
appeared to work and sent this down a long dead end.

Copying the whole 25-byte record sets the marker, the geometry and the flags
together. It's plugin-independent — the editor resizes to whatever the plugin
reports on load, so the donor's 561×410 doesn't carry over. Verified on plugins
with much larger and much smaller editors.

## A method note, because it cost real time

Mid-investigation a patch "worked" on `Q3 Mono` and didn't on anything else. The
two files were byte-identical in the flag region. The difference wasn't the file —
it was that Q3 Mono had been dragged in and toggled by hand earlier in the same FL
session, and FL was reusing its own in-memory wrapper state.

**Never test a patch on a plugin you've already touched in that session.** Use a
plugin you have never loaded, and restart FL between tests, or you can't tell your
patch from the host's memory of what you did.

## Scope

- Confirmed on FL Studio 2025 v25.2.3 build 5171.
- Confirmed on Waves V17 / WaveShell1-VST3 16.7 entries.
- The record layout is the *wrapper's*, not Waves-specific, so it should hold for
  any VST plugin FL wraps — but only Waves entries were patched in anger here.
- If `id 2` isn't 25 bytes on your install, `waves-bridge.py` skips the file
  rather than corrupting it. Open an issue with the length it reports.
