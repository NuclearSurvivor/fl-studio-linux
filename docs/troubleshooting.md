# Troubleshooting

## Prefix basics

Give FL its own Wine prefix. Don't share `~/.wine`. Anything installed later for
another app can wreck a working DAW prefix.

### `WINEPREFIX` points at the folder that *contains* `drive_c`

Point it at `~/flstudio/drive_c` instead of `~/flstudio` and Wine doesn't error —
it silently builds a second empty prefix *inside* the first. FL opens with no
presets, no recent projects, no plugins. Nothing is lost, but it looks like
everything is.

```bash
ls -d "$WINEPREFIX"/drive_c/drive_c 2>/dev/null && echo "doubled prefix"
```

Recover by fixing the variable, then merging the stray tree back without
overwriting anything newer:

```bash
rsync -av --ignore-existing "$WINEPREFIX/drive_c/drive_c/" "$WINEPREFIX/drive_c/"
```

Diff before deleting. `users/` is the half you'll think of. **`Program Files` is
the half people forget**, and deleting the doubled tree without merging it takes
your plugin binaries with it.

A doubled prefix also leaves a stale `~/Documents/Image-Line/...` tree that FL
never reads — see [waves.md](waves.md#find-the-right-plugin-database).

## The "missing files" dialog is always blank

FL says "X sample(s) required by this project could not be located" above a
completely empty list box. The selection highlight paints and the scrollbar is
sized for real rows — only the text never appears. Same for the missing-plugins
version.

Reproduces on a fresh FL install in a fresh prefix. **It is not your setup.**

Not a colour problem — inverting `WindowText` blanks Wine's own file dialogs and
leaves FL's list unchanged. Can't be tested with `uxtheme=d` because FL won't
start without it. No fix known; if you have one, open an issue.

Read the list out of the project file instead. Plugin paths are plain ASCII,
sample paths are UTF-16LE:

```bash
strings    yourproject.flp | grep -iE '\.(dll|vst3|clap)'     | sort -u
strings -el yourproject.flp | grep -iE '\.(wav|mp3|ogg|flac)' | sort -u
strings    yourproject.flp | grep -iE '\.(wav|mp3|ogg|flac)'  | sort -u
```

You get the full path FL expected, which is more than the dialog would have told
you even if it worked.

**FL records the plugin format.** A project naming `Something.clap` will not load
`Something.vst3`, so reinstalling in the wrong format looks like the reinstall
failed.

## Zipped projects

FL opens zipped projects directly, and under Wine that's a common source of
phantom missing samples — they're in the archive, FL's temp extraction just
doesn't resolve them. Extract it yourself and open the `.flp` from the extracted
folder. FL checks the `.flp`'s own folder first.

## Don't do these

### `winetricks comctl32`

On a modern wow64 prefix it installs a **Windows 98-era** DLL and deletes the
Common-Controls 6.0 winsxs manifests. Afterwards every process throws
`Could not find dependent assembly` and `winecfg` itself errors.

Recovery: drop the override (both spellings), delete the DLL from `system32` and
`syswow64`, `wineboot -u`, then copy the manifests back from a clean prefix.
`wineboot` alone does **not** restore them.

### `WINEDLLOVERRIDES="uxtheme=d"`

FL won't start. `unimplemented function uxtheme.dll.GetWindowTheme`.

### `wineserver -k` without checking

Kills every process in the prefix instantly — including a render or a save in
progress, and `WavesLocalServer` with it. The same goes for anything that calls
`wineserver -w`; winetricks does, and it will hang forever waiting for FL to close.

## Smaller ones

**Plugin windows forced to maximum size** — `winecfg` has "Emulate a virtual
desktop" ticked. Untick it.

**FL rejects a sample folder path** — FL won't accept a bare drive root as a
search path. Map the Wine drive one level higher and add a subfolder.

**Can't delete entries in FL's plugin manager** — white entries are FL's locked
built-in defaults, orange are user-added. Only the orange ones are yours.

**An installer silently does nothing, and the log says `fixme:powershell:wmain stub`**
— Wine's PowerShell is a stub that exits 0, so the installer's checks "pass" while
doing nothing. See [companion-apps.md](companion-apps.md#powershell-and-the-wow64-trap),
and note you must replace the `syswow64` copy too for 32-bit installers.

**A patch to the plugin database seems to do nothing** — FL caches the database at
startup. Restart it. And make sure you patched the tree inside the prefix, not a
stale copy.
