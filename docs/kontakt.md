# Kontakt / Native Instruments in a DAW that lives in another Wine prefix

Kontakt 8 Player running as a VST3 inside FL Studio, with libraries, under Wine.

The install goes into its **own** prefix via
[selimbucher/native-instruments](https://github.com/selimbucher/native-instruments),
and then the plugin and its data are linked into the DAW's prefix. Nothing about
the DAW prefix is modified beyond symlinks and two registry keys.

Tested with: Kontakt 8 Player 8.14.1, Komplete Start (Analog Dreams), Native Access
2, FL Studio 2025 v25.2.3, wine-staging 11.21 (wow64), Debian.

---

## Why not just install it into the DAW prefix

You can — `ni` takes `--prefix`. But the installer runs winetricks verbs, installs
PowerShell, replaces Wine's `msvcp140` stubs with the real Microsoft runtimes and
sets DLL overrides. That's a lot of change to a prefix that already has a working
DAW and a licensed plugin library in it.

Two prefixes plus symlinks keeps the blast radius at zero and works fine.

## 1. Install into its own prefix

```bash
sudo apt install winetricks cabextract 7zip msitools xvfb xdotool zenity procps pipx
sudo apt install gcc-mingw-w64-i686          # see note below
pipx install git+https://github.com/selimbucher/native-instruments
pipx ensurepath
```

> **Undocumented dependency.** The wheel build fails with
> `ni-wine needs a mingw-w64 compiler (i686-w64-mingw32-gcc)`. The tool compiles a
> small 32-bit Windows MSI shim, because NI's official Kontakt installer doesn't run
> under Wine at all — it replays the MSI file tables instead. `gcc-mingw-w64-i686`
> isn't in the project's listed dependencies on Debian.

Then:

```bash
ni doctor --fix     # registers the native-access:// URL scheme
ni setup            # builds ~/.wine-ni, installs Native Access + NTKDaemon
native-access       # log in, install Kontakt Player and your libraries
```

The login opens a browser and hands the callback back through `native-access://`.
On Firefox you get an "Open Native Access?" prompt — approve it. Same class of
problem as [Cradle's `app.cradle` scheme](cradle.md), already solved by the tool.

Verify standalone before going near the DAW:

```bash
WINEPREFIX=$HOME/.wine-ni wine \
  "$HOME/.wine-ni/drive_c/Program Files/Native Instruments/Kontakt 8/Kontakt 8.exe"
```

Libraries in the browser, a patch that plays. If that doesn't work, nothing below
will.

## 2. Link the plugin into the DAW prefix

```bash
ln -s "$HOME/.wine-ni/drive_c/Program Files/Common Files/VST3/Kontakt 8.vst3" \
      "$DAW/drive_c/Program Files/Common Files/VST3/Kontakt 8.vst3"
```

Rescan plugins. It scans and loads — but the browser will be empty, because
Kontakt's catalogue lives outside the plugin.

(Mapping the whole NI prefix as a drive letter via `dosdevices/k:` and adding a
plugin search path works equally well for the scan. It doesn't help with anything
below, so the single symlink is simpler. If you do map a drive, note that Wine
caches the drive table in the running `wineserver` — a new mapping needs the
prefix's `wineserver -k`, which also kills `WavesLocalServer` if you use Waves.)

## 3. Registry

```bash
WINEPREFIX=$HOME/.wine-ni wine reg export "HKLM\\Software\\Native Instruments" /tmp/ni-hklm.reg /y
WINEPREFIX=$HOME/.wine-ni wine reg export "HKCU\\Software\\Native Instruments" /tmp/ni-hkcu.reg /y
WINEPREFIX=$DAW wine reg import /tmp/ni-hklm.reg
WINEPREFIX=$DAW wine reg import /tmp/ni-hkcu.reg
```

**Import them unchanged.** The obvious move is to rewrite `C:\` to whatever drive
letter you mapped the NI prefix as. Don't — `komplete.db3` stores absolute `C:\`
paths of its own, and you can't rewrite those. Leave the registry on `C:` and make
the DAW's `C:` resolve instead, which is step 4.

The keys are small:

```
HKLM\...\Analog Dreams\ContentDir = C:\users\Public\Documents\Analog Dreams Library
HKLM\...\Kontakt 8\ContentDir     = C:\Program Files\Common Files\Native Instruments\Kontakt 8\
```

## 4. Make the DAW's `C:` resolve into the NI prefix

```bash
NI="$HOME/.wine-ni/drive_c"
FL="$DAW/drive_c"
U="$USER"      # the Wine user inside the prefix

ln -s "$NI/users/Public/Documents/NI Resources"            "$FL/users/Public/Documents/NI Resources"
ln -s "$NI/users/$U/AppData/Local/Native Instruments"      "$FL/users/$U/AppData/Local/Native Instruments"
ln -s "$NI/users/$U/AppData/Roaming/Native Instruments"    "$FL/users/$U/AppData/Roaming/Native Instruments"
ln -s "$NI/ProgramData/Native Instruments"                 "$FL/ProgramData/Native Instruments"

# one per library
ln -s "$NI/users/Public/Documents/Analog Dreams Library"   "$FL/users/Public/Documents/Analog Dreams Library"
```

**Check what already exists before each `ln -s`.** Kontakt creates several of these
directories itself the first time it loads in the DAW prefix, and `ln -s src dir/`
on an existing directory silently drops the link *inside* it instead of replacing
it. Verify with `ls -ld` afterwards — every one should print as a symlink.

## 5. `Common Files\Native Instruments` — link the children, never the parent

```bash
CF="$FL/Program Files/Common Files/Native Instruments"
mkdir -p "$CF"
ln -s "$NI/Program Files/Common Files/Native Instruments/Kontakt 8" "$CF/Kontakt 8"
ln -s "$NI/Program Files/Common Files/Native Instruments/NTK"       "$CF/NTK"
```

**This is the one that will bite you.** That directory contains a `Service Center`
subfolder, and it is **not** NI's alone — Waves writes its licence registrations
there too, one XML per plugin:

```
Service Center/Waves-CLA-76 Stereo.xml
Service Center/Waves-PuigTec EQP1A Stereo.xml
Service Center/NativeAccess.xml
... ~70 files from two unrelated vendors
```

Symlink the parent and the DAW loses every Waves licence file at once. Symlink the
children and merge `Service Center` per file:

```bash
NISC="$NI/Program Files/Common Files/Native Instruments/Service Center"
FLSC="$CF/Service Center"
mkdir -p "$FLSC"
for f in "$NISC"/*; do
  b=$(basename "$f")
  [ -e "$FLSC/$b" ] || ln -s "$f" "$FLSC/$b"
done
```

If other vendors use that folder on your system, the same rule applies — it's a
shared registration directory, so it gets merged, never replaced.

## 6. NTKDaemon has to be running

```bash
pgrep -af NTK
```

If it isn't:

```bash
WINEPREFIX=$HOME/.wine-ni nohup wine \
  "$HOME/.wine-ni/drive_c/Program Files/Common Files/Native Instruments/NTK/NTKDaemon.exe" \
  >/dev/null 2>&1 &
```

**One daemon covers every prefix.** It serves over a localhost socket rather than
Windows IPC, so a daemon started in the NI prefix is reachable from the DAW's
prefix. Starting a second one in the DAW prefix exits with code 53 — the port is
already taken. That exit code is correct behaviour, not a failure.

Treat it like `WavesLocalServer`: something your launcher script starts if it isn't
already up.

## 7. One Kontakt at a time

`komplete.db3` is a SQLite database, opened in WAL mode. The standalone and a plugin
instance cannot both hold it. Whichever gets there first has the catalogue; the
others show an empty browser with **"No results found"** and no error.

So: close the standalone before loading Kontakt in the DAW. If a browser is
unexpectedly empty, `pgrep -afi 'kontakt 8.exe'` before assuming anything is broken.

## Verifying

In a blank project, in this order:

1. One Kontakt instance — library tiles present, a patch loads and plays
2. A Waves plugin — **not** DEMO MODE (that's the `Service Center` merge)
3. A non-Waves plugin — loads as it always did

## What this does not cover

- Only Kontakt 8 Player and Komplete Start were tested. Paid libraries go through
  the same Native Access pipeline, so they should behave the same, but untested.
- Reaktor, Guitar Rig and the rest of Komplete are untested.
- Whether NI updates through Native Access survive the symlinks. They should —
  everything is linked by directory, so updates land in the NI prefix and the DAW
  sees them — but an update that moves a content path would need the links redone.
- Automation and multi-instance behaviour over a long session.
