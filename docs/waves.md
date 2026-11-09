# Waves under Wine

Tested on Waves V17, WaveShell1-VST3 16.7, FL Studio 2025 v25.2.3 build 5171,
wine-staging 11.21 (wow64).

## The symptom

Waves Central installs under Wine like any normal program. FL scans the WaveShell
and lists every plugin in the browser. Insert one and FL dies:

```
Access violation at address ... in module 'WaveShell1-VST3 16.7_x64.vst3'
```

Every plugin, every time, mono or stereo.

## The fix

Load the plugin, open the wrapper's **Processing** tab, tick **Make bridged**.
Tick **External window** too, or the editor lands in the top-left corner of the
screen.

That's the whole fix. UI opens, audio processes, metering animates, automation
responds.

## Why

Bridging moves the plugin out of `FL64.exe` into a separate `ilbridge.exe`
process. Run `pgrep -af ilbridge` with a Waves plugin open:

```
ilbridge.exe -wrapper -address {...} -processid 572
msedgewebview2.exe --embedded-browser-webview=1 --webview-exe-name=ilbridge.exe ...
msedgewebview2.exe --type=gpu-process ...
msedgewebview2.exe --type=utility --utility-sub-type=network.mojom.NetworkService ...
msedgewebview2.exe --type=utility --utility-sub-type=storage.mojom.StorageService ...
msedgewebview2.exe --type=renderer ...
msedgewebview2.exe --type=crashpad-handler ...
```

Waves runs its licensing and UI layer inside an **embedded Chromium** — a full
Edge WebView2 stack, six processes, caching under
`AppData\Roaming\Waves Audio\Caches`.

Loading WaveShell in-process means asking Wine to spin up Chromium inside the
DAW's own address space and survive it. In the bridge host it can fall over on its
own without taking FL down. It still does sometimes — you'll occasionally get an
`ilbridge` access violation dialog at instantiation (`Read of address 0x18`).
Dismiss it, reload the plugin, carry on.

Bridging isn't a workaround for a quirk. It keeps an entire browser out of the
audio process.

## One unbridged instance poisons the session

If you instantiate a Waves plugin **unbridged**, the session is finished. Every
bridged instance after it fails too. Removing it from the mixer doesn't help —
restart FL.

WaveShell does process-global init, and a failed in-process load leaves that state
wrecked for everything that follows. A fresh FL that only ever loads bridged
instances never does the in-process load at all.

This is the real argument for patching the whole database rather than ticking
boxes by hand: once every entry is bridged, you can't misclick into a dead session.

## Making it permanent

Three ways, increasing in power.

### 1. Save a bridged preset

Load it, tick both boxes, wrapper menu → *Save preset as*. Drag that `.fst` from
the browser and it comes in configured.

### 2. Add it to the plugin database

Wrapper menu → *Add to plugin database (flag as favorite)*.

It'll refuse with *"please first select or open the plugin database subcategory
folder"*. That means a subcategory under **Plugin database → Effects** — Dynamics,
Delay reverb, Distortion and so on — **not** the `Installed → Effects → VST3`
tree, which is FL's scan inventory and won't accept writes.

Category entries are ordinary `.fst` files, so you can also copy presets straight
in:

```bash
cp "Fruity Wrapper - CLA-2A Stereo/CLA-2A Stereo BRIDGED.fst" \
   "$DB/Effects/Waves/CLA-2A Stereo.fst"
```

### 3. Patch the whole library

See [fst-format.md](fst-format.md) for what's being changed, and
[`waves-bridge.py`](../waves-bridge.py) for the tool.

Bridge one plugin by hand, tick External window, save it as a preset — that's your
donor. Then:

```bash
# back up first; .fst files are tiny
cd "$HOME" && find . -path '*Plugin database*' -name '*.fst' \
  | tar -czf ~/fl-fst-backup.tar.gz -T -

DB="$WINEPREFIX/drive_c/users/$USER/Documents/Image-Line/FL Studio/Presets/Plugin database/Installed/Effects"
mapfile -d '' W < <(grep -rlZa 'WaveShell' "$DB" --include='*.fst')
echo "${#W[@]} Waves entries"
python3 waves-bridge.py "/path/to/MyPlugin BRIDGED.fst" "${W[@]}"
```

**Filter on `WaveShell`.** Don't patch everything — FabFilter, Soundtoys and
Valhalla load in-process perfectly well and bridging them just costs a process
each. Patching a whole VST3 folder blind caught 42 non-Waves plugins here and they
had to be restored.

Restart FL afterwards. It caches the plugin database at startup.

## Find the right plugin database

FL reads the database from **inside the prefix**:

```
$WINEPREFIX/drive_c/users/$USER/Documents/Image-Line/FL Studio/Presets/Plugin database
```

If a `~/Documents/Image-Line/...` tree also exists on the Linux side — a leftover
from a doubled prefix, see [troubleshooting.md](troubleshooting.md) — it is **not**
the same tree and FL never reads it. Three hours went into patching the wrong one
here before anyone noticed.

Check the Path field in FL's browser info panel before trusting any path.

## Two things that have to be true

**`WavesLocalServer` must be running.** It's the licensing daemon and it does
*not* autostart when you launch `wine FL64.exe` directly. `wineserver -k` kills
it. Without it, Waves loads in DEMO MODE and it looks like the whole thing failed.

```bash
pgrep -af WavesLocalServer
```

**The licence has to be on this machine.** A VM counts as a separate machine.
Deactivate on the VM, let Waves Central finish downloading on Linux, then
activate there.

## What works

| Action | Works |
|---|---|
| Insert fresh from the plugin browser | Yes |
| Duplicate a loaded instance to another track | Yes |
| Drag a loaded plugin's preset to another slot | Yes |
| Save as `.fst`, load the `.fst` | Yes |
| Open a Windows-saved project on Linux | Yes |
| Re-save on Linux and reopen | Yes |
| Insert **unbridged** | No — and it kills the session until FL restarts |

## Untested

- Waves V14 / V15 / V16 — only V17 here
- VST2 shells — VST3 throughout
- Whether bridging solves Waves in other DAWs under Wine. Reaper, Bitwig and
  Ableton all have their own sandboxing or bridging. Someone reported that
  Renoise's plugin sandboxing fixed WaveShell crashes on *Windows*, which is what
  pointed at this in the first place. If you try it, open an issue.
- Whether automation on bridged instances behaves over a long session
- Whether any of it survives an FL update

---

## Verify the patch — and mind the hidden folder

Two things bit me hours after I thought this was finished.

**Restoring the hidden entries silently undoes the patch.** Earlier advice (mine included)
was to move the Waves database entries into a hidden folder so you couldn't misclick into
a crash. Those copies are *pre-patch*. Move them back and every entry you patched is
overwritten with an unbridged one. I did exactly this, and an hour later Waves started
crashing again with the whole database back to 302 of 302 unbridged. Patch the hidden
folder as well, or delete it once you don't need it.

**Check the end state, not the script's output.** `patched 302` tells you what the script
wrote. It does not tell you what the database now contains — something else may have
overwritten it since. This does:

```bash
cd "$DB"
mapfile -d '' UNPATCHED < <(
  grep -rlZa 'WaveShell' . --include='*.fst' |
  while IFS= read -r -d '' f; do
    python3 tools/fst-inspect.py flags "$f" 2>/dev/null | grep -qE 'bridged +yes' \
      || printf '%s\0' "$f"
  done
)
echo "${#UNPATCHED[@]} unpatched of $(grep -rla 'WaveShell' . --include='*.fst' | wc -l)"
```

Note the null delimiters. Waves filenames contain spaces, and a plain
`for f in $(grep -rl ...)` splits `Enigma Stereo.fst` into two bogus paths — I wrote that
bug and spent a minute reading garbage output before noticing.

Zero is the only acceptable answer. Run it before and after any database work.

## Telling the two Waves failures apart

They have different causes and different fixes:

| Dialog | Means | Fix |
|---|---|---|
| `Access violation ... in WaveShell1-VST3` | in-process load, plugin isn't bridged at instantiation | bridge it |
| `crashed while loading its settings` | FL couldn't deserialise the wrapper record — the entry is unpatched or corrupt | check it with `fst-inspect flags`, re-patch |
| Loads but says DEMO | `WavesLocalServer` isn't running | `pgrep -af WavesLocalServer` |

Either of the first two also poisons the session: every Waves instance after it fails until
you restart FL.
