# FL Studio on Linux, with Waves

A working record of getting a full commercial plugin setup running in FL Studio
under Wine — including **Waves, loading normally from the plugin browser**, which
as far as I can find is not documented anywhere else.

**Setup this was built and tested on**

| | |
|---|---|
| OS | Debian |
| Wine | wine-staging 11.21 (wow64) |
| DAW | FL Studio Producer Edition v25.2.3 build 5171, All Plugins, Windows 64-bit |
| Audio | PipeWire |
| Hardware | Ryzen 9 5900X · 32 GB 3200 MHz · Samsung 990 Pro 2 TB NVMe · RTX 3080 |

I ran FL on Linux for about a year believing a serious setup wasn't possible here.
It is. Most of what follows had one-line answers that took a long time to find.

---

## The short version

**Waves crashes FL on insert because WaveShell loads in-process, and Waves runs an
entire embedded Chromium (Edge WebView2, six processes) for its licensing and UI
layer.** Tick **Make bridged** in the plugin wrapper's Processing tab and it loads
in `ilbridge.exe` instead, where it can misbehave without taking the DAW with it.

To make that the default for a whole library, the setting lives in the `.fst`
plugin-database entries — **event 213, record `id 2`, 25 bytes**:

```
byte 0       settings-valid marker
bytes 1-4    editor width   (int32 LE)
bytes 5-8    editor height  (int32 LE)
byte 10      bit 0x02  ->  Make bridged
byte 11      bit 0x04  ->  Make bridged (companion)
byte 11      bit 0x20  ->  External window
```

**Copy the whole record, don't flip the bits.** FL ships every scan entry with the
marker clear and the editor rectangle at `-1 / -1`, and it won't apply a window
flag to a rectangle that doesn't exist — so a partial patch gets you bridging and
nothing else. [Full writeup →](docs/fst-format.md)

304 Waves plugins now load straight from the browser here. No Windows VM, no
project templates, no round trip.

**Kontakt 8 also runs**, installed into its own prefix and linked into FL's — see
[kontakt.md](docs/kontakt.md). The trap there is that Waves and Native Instruments
share one `Service Center` registration folder, so it has to be merged per file.

---

## Quick start

```bash
git clone https://github.com/<you>/fl-studio-linux
cd fl-studio-linux
```

1. In FL, load any Waves plugin, open the wrapper's **Processing** tab, tick
   **Make bridged** and **External window**.
2. Wrapper menu → *Save preset as*. That file is your donor.
3. Back up, then patch every Waves entry in the plugin database:

```bash
# back up - .fst files are tiny, the whole database is ~20 MB
cd "$HOME" && find . -path '*Plugin database*' -name '*.fst' \
  | tar -czf ~/fl-fst-backup.tar.gz -T -

DB="$WINEPREFIX/drive_c/users/$USER/Documents/Image-Line/FL Studio/Presets/Plugin database/Installed/Effects"
mapfile -d '' W < <(grep -rlZa 'WaveShell' "$DB" --include='*.fst')
echo "${#W[@]} Waves entries"
python3 waves-bridge.py "/path/to/MyPlugin BRIDGED.fst" "${W[@]}"
```

4. Restart FL. It caches the plugin database at startup.

`--dry-run` shows what would change without writing. Anything whose settings
record isn't the expected size is skipped, not corrupted.

> **Filter on `WaveShell`.** FabFilter, Soundtoys and Valhalla load in-process
> perfectly well and bridging them just costs a process each.

> **Patch the tree inside the prefix.** If a `~/Documents/Image-Line/...` tree
> also exists, FL never reads it. Check the Path field in FL's browser info panel.
> Three hours went into the wrong tree here.

---

## Docs

| | |
|---|---|
| [**Waves**](docs/waves.md) | the crash, why bridging fixes it, the session-poisoning trap, three ways to make it permanent |
| [**`.fst` format**](docs/fst-format.md) | the container, event 213, record `id 2`, and a method note about testing on contaminated targets |
| [**Plugin compatibility**](docs/plugins.md) | what works, what doesn't, what to expect — with the rule that predicts it |
| [**Audio**](docs/audio.md) | PipeWire channel maps, crackling, quantum, realtime priority, latency |
| [**Graphics**](docs/graphics.md) | check the GPU is alive before blaming Wine; DXVK, and what it doesn't fix |
| [**Kontakt / NI**](docs/kontakt.md) | Kontakt 8 as a VST3 in a DAW that lives in a *different* Wine prefix, with libraries |
| [**Cradle Hub**](docs/cradle.md) | blank window, and the `app.cradle` URL scheme |
| [**Troubleshooting**](docs/troubleshooting.md) | doubled prefixes, the blank missing-files dialog, things not to run |

## Tools

| | |
|---|---|
| [`waves-bridge.py`](waves-bridge.py) | the patcher |
| [`tools/fst-inspect.py`](tools/fst-inspect.py) | `events` / `records` / `flags` / `diff` — how all of this was worked out |
| [`examples/fl`](examples/fl) | launcher that sets the PipeWire bits before starting FL |

```bash
# what did ticking that checkbox actually change?
python3 tools/fst-inspect.py diff "before.fst" "after.fst"

# is this database entry bridged?
python3 tools/fst-inspect.py flags "$DB/Installed/Effects/VST3/CLA-2A Stereo.fst"
```

---

## The rule worth taking away

**It isn't copy protection that breaks under Wine — it's copy protection that
needs a separate companion application.**

Soundtoys and oeksound Soothe use the same PACE licensing. Soundtoys activates
with a code typed into the plugin window and worked first try. Soothe needs iLok
License Manager as a separate app, and PACE's installer aborts under Wine.

Before buying anything: does it activate inside the plugin, or does it need a
manager app? That predicts Wine behaviour better than price or publisher.
[Full table →](docs/plugins.md)

---

## Scope and honesty

Everything here was tested on one machine, one FL version, one Waves version. The
[compatibility table](docs/plugins.md) marks what was used in real work versus what
merely loads. Untested things are marked untested rather than guessed at.

Known not working: **oeksound Soothe 3** — iLok License Manager won't install, and
its editor needs `CreateSwapChainForComposition`, which DXVK doesn't implement.

If you get something working that's listed here as untested or broken, please open
an issue. The table exists to stop other people repeating dead ends.

## Prior art and credits

- [tillrd/waves-linux](https://github.com/tillrd/waves-linux) — the one existing
  Waves-on-Linux guide I found. Different approach: Waves into a *native* Linux
  DAW via yabridge, skipping Waves Central. Worth reading.
- [yabridge](https://github.com/robbert-vdh/yabridge) — if your DAW is native,
  use this instead of running the whole host under Wine.
- [DXVK](https://github.com/doitsujin/dxvk) · [WineHQ](https://www.winehq.org) ·
  [winetricks](https://github.com/Winetricks/winetricks)
- The pointer that cracked Waves: a report that enabling **Renoise's plugin
  sandboxing** fixed WaveShell crashes on Windows. Bridging is FL's equivalent.

## Licence

[MIT](LICENSE). The documentation is findings about other people's software; the
code is mine. No affiliation with Image-Line, Waves, or anyone else named here.
