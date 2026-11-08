# Plugins that need a companion app

Native Access, Arturia Software Center, Slate's Complete Access Hub, iLok License
Manager. The conventional wisdom is that these don't work under Wine and so neither
do the plugins behind them.

**All four work.** The pattern below has now run four times with four different
vendors.

---

## The pattern

1. **Install into its own Wine prefix**, never the DAW's. The installers run
   winetricks verbs, install runtimes, set DLL overrides. Keep that away from a
   prefix holding a working DAW and a licensed plugin library.
2. **Get it working standalone first.** If the vendor ships a standalone, prove it
   renders and makes sound there. Every failure after that is an integration
   problem, not a plugin problem.
3. **Symlink the `.vst3` into the DAW's prefix**, into
   `Program Files/Common Files/VST3/`. Subfolders are scanned, so a vendor folder
   can be linked whole.
4. **Symlink the data directories** so the DAW's `C:` resolves them — content,
   `ProgramData`, `AppData`. Absolute `C:\` paths are baked into databases and
   config you can't rewrite, so make `C:` resolve rather than rewriting paths.
5. **Export and import the registry** keys under `HKLM\Software\<Vendor>` and
   `HKCU\Software\<Vendor>`. Import **unchanged** — see point 4.
6. **Check for shared directories before linking a parent.** See the warning below.

Worked examples: [Kontakt / Native Instruments](kontakt.md) and the two below.

---

## Warning: shared registration directories

`Program Files\Common Files\Native Instruments\Service Center` is **not** NI's alone.
Waves writes its licence registrations there too — about 70 XML files, one per
plugin.

Symlink that parent directory and you silently destroy Waves licensing. Link the
*children* and merge the shared folder file by file:

```bash
for f in "$SRC/Service Center"/*; do
  b=$(basename "$f")
  [ -e "$DST/Service Center/$b" ] || ln -s "$f" "$DST/Service Center/$b"
done
```

Check what's in a directory before you link it. The name of the folder tells you
which vendor created it, not which vendors use it.

---

## PowerShell, and the WOW64 trap

Several installers shell out to PowerShell. Wine ships a **stub** that prints
`fixme:powershell:wmain stub` and **exits 0** — so an installer's check "succeeds"
while doing nothing, and a naive `echo $?` test looks like it passed.

Real PowerShell 7 can be installed into a prefix.
[ni-wine](https://github.com/selimbucher/native-instruments) does it as part of
`ni setup`, which makes `~/.wine-ni` a convenient donor:

```bash
NI="$HOME/.wine-ni/drive_c"
DST="$HOME/.wine-<target>/drive_c"

cp -r "$NI/Program Files/PowerShell" "$DST/Program Files/"
cp "$NI/windows/system32/WindowsPowerShell/v1.0/powershell.exe" \
   "$DST/windows/system32/WindowsPowerShell/v1.0/powershell.exe"
```

**Then do it again for `syswow64`:**

```bash
cp "$NI/windows/system32/WindowsPowerShell/v1.0/powershell.exe" \
   "$DST/windows/syswow64/WindowsPowerShell/v1.0/powershell.exe"
```

Most installers are 32-bit. Under WOW64 file-system redirection, a 32-bit process
asking for `C:\windows\system32\...` is silently served `syswow64` instead. Replace
only the 64-bit copy and your own tests pass while the installer keeps getting the
stub — which is exactly what happened here, twice.

Verify with output, not exit codes:

```bash
WINEPREFIX=$DST_PREFIX wine powershell -NoProfile -C "Write-Output HELLO" 2>/dev/null
```

`HELLO` means real PowerShell. The stub prints nothing and still exits 0.

---

## Arturia (Pigments)

[arturia.com](https://www.arturia.com) · Pigments 7.0.1 · **works**

```bash
export WINEPREFIX=$HOME/.wine-arturia
wineboot -i
winetricks -q win10
wine ~/Downloads/Pigments__7_0_1_6772.exe     # installs Arturia Software Center too
```

Take the `.pkg` warning: Arturia's download page offers macOS `.pkg` and Windows
`.exe`. Wine needs the `.exe`.

The standalone renders and plays with no configuration. Linking into the DAW:

```bash
A="$HOME/.wine-arturia/drive_c"; FL="$DAW/drive_c"
ln -s "$A/Program Files/Common Files/VST3/Pigments.vst3" "$FL/Program Files/Common Files/VST3/Pigments.vst3"
ln -s "$A/ProgramData/Arturia"         "$FL/ProgramData/Arturia"
ln -s "$A/ProgramData/ArturiaSC"       "$FL/ProgramData/ArturiaSC"
ln -s "$A/Program Files/Arturia"       "$FL/Program Files/Arturia"
ln -s "$A/Program Files (x86)/Arturia" "$FL/Program Files (x86)/Arturia"

WINEPREFIX=$HOME/.wine-arturia wine reg export "HKLM\\Software\\Arturia" /tmp/art.reg /y
WINEPREFIX=$DAW wine reg import /tmp/art.reg
```

Arturia writes nothing into `Common Files`, so there's no collision to worry about.

**One quirk:** in FL the embedded editor glitches — hovering or dragging makes it go
transparent and show what's behind it. Tick **Make bridged** *and* **External
window** in the wrapper's Processing tab and it's perfect. The renderer is fine; the
problem is how the editor surface is parented inside the host window.

Make it the default with the [`id 2` transplant](fst-format.md) — that mechanism is
not Waves-specific:

```bash
G="$DAW/drive_c/users/$USER/Documents/Image-Line/FL Studio/Presets/Plugin database/Installed/Generators"
python3 tools/fstid2.py "<donor.fst>" "$G/VST3/Pigments.fst" "$G/New/Pigments.fst"
```

---

## Slate Digital (Complete Access Hub)

[slatedigital.com](https://slatedigital.com) · Complete Access Hub 2.27.0 · **works**

Needs the PowerShell fix above — the Hub's installer makes several PowerShell calls,
including `Get-CimInstance Win32_Process`, and it's a 32-bit installer, so the
`syswow64` copy is the one that matters.

```bash
export WINEPREFIX=$HOME/.wine-slate
wineboot -i
winetricks -q win10
# ... PowerShell copy, including syswow64 ...
wine ~/Downloads/"Complete Access Hub Setup 2.27.0.exe"
```

The Hub then runs, signs in, shows your products and installs them. Plugins land in
`Program Files/Common Files/VST3/Slate Digital/`.

Linking is simple — Slate keeps nothing in the registry because licensing is entirely
iLok:

```bash
S="$HOME/.wine-slate/drive_c"; FL="$DAW/drive_c"
ln -s "$S/Program Files/Common Files/VST3/Slate Digital" "$FL/Program Files/Common Files/VST3/Slate Digital"
ln -s "$S/ProgramData/Slate Digital"                     "$FL/ProgramData/Slate Digital"
```

Then activate the licence to the machine in [iLok License Manager](ilok.md) and
rescan. Fresh Air loads, renders and processes audio.

---

## What this leaves

The companion app is no longer a reliable predictor of failure. Four for four.

What *does* predict failure is the renderer — see
[JUCE 8 blank windows](graphics.md#juce-8-blank-windows). A plugin can install,
authorise and process audio perfectly and still be unusable because its editor
can't draw.

Untested with this pattern: iZotope Product Portal, reFX Cloud, UA Connect,
Spectrasonics' installers.

---

## Keeping track of the prefixes

Four or five prefixes is enough that "which one am I in" becomes a real source of
mistakes, and the usual answer — `pgrep -f wineserver` — does not work. wineserver's
command line carries no prefix; the prefix comes in through the environment. So
grepping the process list reports every prefix idle, running ones included.

The signal that does work is the socket, whose path wineserver derives from the
prefix directory's device and inode:

```bash
d=$(stat -c '%d' "$WINEPREFIX"); i=$(stat -c '%i' "$WINEPREFIX")
sock="/tmp/.wine-$(id -u)/server-$(printf '%x' "$d")-$(printf '%x' "$i")/socket"
[ -S "$sock" ] && echo LIVE || echo idle
```

[`examples/fl-aliases.sh`](../examples/fl-aliases.sh) wraps that as `wp`, along with
a launcher per application and `wpkill` for clearing a wedged prefix. A stale
wineserver left over from an earlier install is a common cause of an installer
behaving differently the second time you run it, and it is invisible until you look
for it.
