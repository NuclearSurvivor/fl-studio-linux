**Everything in this post, as a repo:** [github.com/NuclearSurvivor/fl-studio-linux](https://github.com/NuclearSurvivor/fl-studio-linux) — the patcher script, an `.fst` inspector, and the long-form version of every section here.

**Setup:** Debian · wine-staging 11.21 (wow64) · FL Studio Producer Edition v25.2.3 build 5171, All Plugins Edition, Windows 64-bit · PipeWire
**Hardware:** Ryzen 9 5900X · 32 GB 3200 MHz · Samsung 990 Pro 2 TB NVMe · RTX 3080

I run FL on Linux full time. I spent about a year believing a serious setup wasn't possible here — especially Waves.

**Major edit 1.** The first version of this post said Waves only worked by authoring projects in a Windows VM and moving the `.flp` across. That is obsolete. Waves now instantiates normally from the plugin browser — all 304 of them, no VM, no round trip, no template. The Waves section below is rewritten from scratch.

**Major edit 2.** This post used to say iLok License Manager won't install under Wine, and built a prediction rule on top of that: copy protection needing a separate companion app is what breaks. **Both of those were wrong and I've rewritten them.** iLok License Manager installs and runs. So do Native Access, Arturia Software Center and Slate's Complete Access Hub — four for four. Kontakt 8, Arturia Pigments and Slate's Fresh Air all now run in FL here.

The real blocker turned out to be something else entirely: **plugins built with JUCE 8 draw a blank window under Wine**, licensing intact, audio working. That's what actually stops Soothe 3, not iLok. New sections below, and every addition in this round is marked **[edit 2]**.

Writing up everything, because most of it isn't documented anywhere and I lost a lot of hours to obstacles that turned out to have one-line answers.

---

# How I installed everything

I originally installed FL Studio through **Lutris**. It works, but that setup is also where my doubled-prefix problem came from (next section), and I don't use it anymore. These days I launch FL straight from a small shell script with `wine`, no launcher app in the middle. That's at the bottom of this post.

**Every plugin installed the same boring way** — point `WINEPREFIX` at the FL prefix and run the Windows installer:

    WINEPREFIX=$HOME/flstudio wine ~/Downloads/SomeInstaller.exe

That's it. Waves Central included. It installed like any normal program, no tricks, no special verbs. Same for Soundtoys, FabFilter, Valhalla and Vital. Cradle needed extra work — separate section below.

Take VST3 and skip AAX — that's Pro Tools only and FL can't load it.

**On the FL licence:** same Image-Line licence on the Linux install and the Windows VM. I didn't need a second one.

---

# Prefix basics

Give FL its own Wine prefix. Don't share `~/.wine`. Anything you install later for another app can wreck a working DAW prefix, and a separate one costs nothing.

**`WINEPREFIX` points at the folder that *contains* `drive_c`, not at `drive_c` itself.**

This one cost me a month. Point it at `~/flstudio/drive_c` instead of `~/flstudio` and Wine doesn't error — it silently builds a second empty prefix *inside* the first. FL opens with no presets, no recent projects, no plugins. Nothing is lost, but it looks like everything is.

Check for it:

    ls -d "$WINEPREFIX"/drive_c/drive_c 2>/dev/null && echo "doubled prefix"

To recover: fix the variable, then merge the stray tree back without overwriting anything newer.

    rsync -av --ignore-existing "$WINEPREFIX/drive_c/drive_c/" "$WINEPREFIX/drive_c/"

Then diff before deleting. `users/` is the half you'll think of. `Program Files` is the half people forget, and deleting the doubled tree without merging it takes your plugin binaries with it.

**One more:** when checking `HKCU\Software\Wine\DllOverrides`, note that winetricks writes some entries with a **leading asterisk** — `*dxgi`, `*d3d11`. A `reg delete` on the unprefixed name reports success and changes nothing, so you'll think an override is gone when it's still live. Always `reg query` the key instead of trusting a delete.

---

# Waves: fully working, straight from the browser

I'm on **Waves V17, WaveShell1-VST3 16.7**. I'd expect this to hold for other versions since it's not version-specific behaviour as far as I can tell, but V17 is what I actually tested.

Waves Central installs under Wine like any other program. FL scans the WaveShell and lists every plugin in the browser. Then you insert one and FL dies:

    Access violation at address ... in module 'WaveShell1-VST3 16.7_x64.vst3'

Every plugin, every time, mono or stereo.

### The fix is one checkbox

Load the plugin, open the wrapper's **Processing** tab, tick **Make bridged**. That's it. UI opens, audio processes, metering animates, automation responds. Tick **External window** too or the editor lands in the top-left corner of your screen.

Bridging moves the plugin out of `FL64.exe` into a separate `ilbridge.exe` process.

### Why: Waves runs a browser inside your DAW

Run `pgrep -af ilbridge` with a Waves plugin open:

    ilbridge.exe -wrapper -address {...} -processid 572
    msedgewebview2.exe --embedded-browser-webview=1 --webview-exe-name=ilbridge.exe ...
    msedgewebview2.exe --type=gpu-process ...
    msedgewebview2.exe --type=utility --utility-sub-type=network.mojom.NetworkService ...
    msedgewebview2.exe --type=utility --utility-sub-type=storage.mojom.StorageService ...
    msedgewebview2.exe --type=renderer ...
    msedgewebview2.exe --type=crashpad-handler ...

**Waves runs its licensing and UI layer inside an embedded Chromium** — a full Edge WebView2 stack, six processes, caching under `AppData\Roaming\Waves Audio\Caches`. Loading WaveShell in-process means asking Wine to spin up Chromium inside your DAW's own address space and survive it.

In the bridge host it can fall over on its own without taking FL with it — and it does, sometimes. You'll occasionally get an `ilbridge` access violation dialog at instantiation (`Read of address 0x18`). Dismiss it, reload the plugin, it's fine.

So bridging isn't a workaround for a quirk. It's keeping an entire browser out of your audio process.

### One unbridged instance poisons the whole session

This matters and it cost me an hour of false results.

If you instantiate a Waves plugin **unbridged**, the session is finished. Every bridged instance after it also fails. Removing it from the mixer doesn't help — you have to restart FL. WaveShell does process-global init, and a failed in-process load leaves that state wrecked for everything that follows.

A fresh FL that only ever loads bridged instances never does the in-process load at all, and nothing ever breaks. Which is the real argument for patching the whole database rather than ticking boxes by hand — once every entry is bridged, you can't misclick into a dead session.

### Making it stick

Ticking a box per instance is fine once. Three ways to make it the default, increasing in power:

**1. Save a bridged preset.** Load it, tick Make bridged and External window, wrapper menu → *Save preset as*. Drag that `.fst` from the browser and it comes in configured.

**2. Put it in the plugin database.** Wrapper menu → *Add to plugin database (flag as favorite)*. It'll refuse with "please first select or open the plugin database subcategory folder." It means a subcategory under **Plugin database → Effects** — Dynamics, Delay reverb, Distortion, and so on — **not** the `Installed → Effects → VST3` tree, which is FL's scan inventory and won't accept writes. Pick Dynamics for a compressor and it works.

Those category entries are ordinary `.fst` files, so you can also just copy presets in:

    cp "Fruity Wrapper - CLA-2A Stereo/CLA-2A Stereo BRIDGED.fst" \
       "$DB/Effects/Waves/CLA-2A Stereo.fst"

**3. Patch the entire library at once.** This is the part nobody has published.

### The `.fst` format

An `.fst` is an FLP event stream: `FLhd` header, `FLdt` chunk, then events. Event `213` is the plugin wrapper. Its payload is a list of records, each `id (int32) · length (int64) · data`:

    id  2   25 B    wrapper settings      <- this one
    id 50   16 B
    id 52   16 B    VST3 class ID         e.g. "MTSVDOmMondomod "
    id 53    *      plugin state blob     (presets only)
    id 54   24 B    "WaveShell1-VST3 16.7_x64"
    id 55   64 B    "C:\Program Files\Common Files\VST3\WaveShell1-VST3 16.7_x64.vst3"
    id 56    5 B    "Waves"

Record **id 2** is the wrapper settings, 25 bytes:

    byte 0       settings-valid marker
    bytes 1-4    editor width   (int32 LE)
    bytes 5-8    editor height  (int32 LE)
    byte 10      bit 0x02  ->  Make bridged
    byte 11      bit 0x04  ->  Make bridged (companion)
    byte 11      bit 0x20  ->  External window

A working bridged + detached record:

    01 31 02 00 00 9a 01 00 00 8c 7f 24 b4 00 00 00 00 01 00 00 00 00 00 00 00
    ^^ ^^^^^^^^^^^ ^^^^^^^^^^^    ^^ ^^
    |  width 561   height 410     |  bridged | external
    marker set                    bridged

Every scan entry FL generates looks like this instead:

    00 ff ff ff ff ff ff ff ff 08 7d 50 00 00 00 00 00 01 00 00 00 00 00 00 00
    ^^ ^^^^^^^^^^^^^^^^^^^^^^^
    |  geometry = -1 / -1
    marker clear

**That's the trap.** Set bit `0x02` at byte 10 and bridging starts working immediately. Set bit `0x20` at byte 11 for External window and FL silently throws it away — because byte 0 is clear and the window rectangle is -1/-1, and FL won't apply a window flag to a rectangle that doesn't exist. I burned two hours setting that bit correctly over and over.

**So I stopped setting bits and transplanted the whole 25-byte record instead** — copy `id 2` wholesale out of a working bridged preset and overwrite the target's. That's what finally worked, and it's what the script below does. I worked the layout out by saving one plugin twice, bridged and unbridged, and diffing the two files byte by byte until the record boundaries fell out.

It's plugin-independent — the window auto-sizes to whatever the plugin actually reports on load, so the donor's geometry doesn't carry over.

**[edit 2]** This isn't a Waves-specific trick. `id 2` is FL's wrapper defaults for *any* plugin, so the same transplant sets bridging and external-window on anything in your database. I've since used it for Arturia Pigments, which needs both for a different reason — see the companion-app section.

    #!/usr/bin/env python3
    # waves-bridge.py <donor.fst> <database .fst files...>
    import sys, struct

    def wrapper(d):
        pos = 8 + struct.unpack_from('<I', d, 4)[0]
        end = pos + 8 + struct.unpack_from('<I', d, pos + 4)[0]
        pos += 8
        while pos < end:
            ev = d[pos]; pos += 1
            if   ev <  64: pos += 1
            elif ev < 128: pos += 2
            elif ev < 192: pos += 4
            else:
                n = shift = 0
                while True:
                    b = d[pos]; pos += 1
                    n |= (b & 0x7F) << shift; shift += 7
                    if not b & 0x80: break
                if ev == 213: return pos, n
                pos += n
        return None, None

    def settings(d, o, n):
        end, p = o + n, o
        while p + 12 <= end:
            fid = struct.unpack_from('<I', d, p)[0]
            ln  = struct.unpack_from('<Q', d, p + 4)[0]
            if 0 < fid < 4096 and 0 < ln <= end - (p + 12):
                if fid == 2: return p + 12, ln
                p += 12 + ln
            else:
                p += 1
        return None, None

    src = open(sys.argv[1], 'rb').read()
    so, sn = wrapper(src)
    sp, sl = settings(src, so, sn)
    print('donor record:', src[sp:sp + sl].hex(' '))

    n = 0
    for t in sys.argv[2:]:
        d = bytearray(open(t, 'rb').read())
        if d[0:4] != b'FLhd': continue
        o, ln = wrapper(d)
        if o is None: continue
        p, l = settings(d, o, ln)
        if p is None or l != sl: continue
        d[p:p + l] = src[sp:sp + sl]
        open(t, 'wb').write(d); n += 1
    print(n, 'patched')

Bridge one plugin by hand, save it as a preset, then point the script at every Waves entry:

    DB="$WINEPREFIX/drive_c/users/$USER/Documents/Image-Line/FL Studio/Presets/Plugin database/Installed/Effects"
    mapfile -d '' W < <(grep -rlZa 'WaveShell' "$DB" --include='*.fst')
    echo "${#W[@]} Waves entries"
    python3 waves-bridge.py "/path/to/YourPlugin BRIDGED.fst" "${W[@]}"

Back up first — `.fst` files are tiny, my whole database tars to about 20 MB:

    cd "$HOME" && find . -path '*Plugin database*' -name '*.fst' \
      | tar -czf ~/fl-fst-backup.tar.gz -T -

**Filter on `WaveShell`.** Don't patch everything. FabFilter, Soundtoys and Valhalla load in-process perfectly well and bridging them just costs you a process each. I patched my whole VST3 folder by accident and had to restore 42 entries.

Restart FL afterwards — it caches the plugin database at startup, so nothing you patch takes effect in a running session.

### Find the right plugin database

FL reads the database from **inside the prefix**:

    $WINEPREFIX/drive_c/users/$USER/Documents/Image-Line/FL Studio/Presets/Plugin database

If you also have `~/Documents/Image-Line/...` on the Linux side — I did, left over from the doubled-prefix mess — it is **not** the same tree and FL never reads it. I patched that one for three hours and concluded the flag didn't work. Check the Path field in FL's browser info panel before you trust any path.

### Two things that still have to be true

**`WavesLocalServer` must be running.** It's the licensing daemon, and it does *not* autostart when you launch `wine FL64.exe` directly. A `wineserver -k` also kills it. Without it, Waves loads in DEMO MODE and you'll think the whole thing failed.

    pgrep -af WavesLocalServer

**Your licence has to be on this machine.** A VM counts as a separate machine. I deactivated the Waves licence on the Windows VM, then reactivated it on the Linux desktop once Waves Central had finished downloading everything. Took a minute.

### What works now

| Action | Works |
|---|---|
| Insert fresh from the plugin browser | **Yes** |
| Duplicate a loaded instance to another track | **Yes** |
| Drag a loaded plugin's preset to another slot | **Yes** |
| Save as .fst, load the .fst | **Yes** |
| Open a Windows-saved project on Linux | Yes |
| Re-save it on Linux, reopen | Yes |
| Insert **unbridged** | No — and it kills the session until you restart FL |

The old version of this post told you to hide the browser entries so you couldn't misclick into a crash. Unhide them:

    mv ~/fl-waves-db-hidden/*.fst "$DB/Installed/Effects/VST3/"

then run the patch over them.

### Prior art

[tillrd/waves-linux](https://github.com/tillrd/waves-linux) is the one existing guide I found and it's worth reading, but it's a different setup — they bridge Waves into a *native* Linux DAW with yabridge, and they skip Waves Central entirely because they say it doesn't work under Wine. I'm running the whole host under Wine, and Central installed for me normally.

Neither that guide nor anything else I could find describes the instantiation crash, the bridging fix, or the `id 2` record. If someone's documented it somewhere, link me and I'll credit it.

---

# Plugin compatibility

**Works, no issues:** FabFilter (whole range), Soundtoys, Valhalla, Vital, Serum 2

**Works after setup:**

* Waves — bridged, as above
* Cradle (God Particle / The Spirit / The Prince) — needs the Hub sign-in fix below
* **[edit 2]** Kontakt 8 + libraries — own prefix, symlinked into FL's
* **[edit 2]** Arturia Pigments — needs bridged + external window
* **[edit 2]** Slate Digital Fresh Air — own prefix, licensed through iLok

**Licensed but unusable:** **[edit 2]** Soothe 3 — installs, authorises, processes audio, and draws a blank editor. JUCE 8, not iLok. Section below.

**Untested:** Nexus 4, iZotope, Universal Audio, Spectrasonics, Plugin Alliance.

### [edit 2] The rule I had here was wrong

The old version of this section said: *it isn't copy protection that breaks under Wine, it's copy protection that needs a separate companion application.* I'd tested exactly one companion app, failed to install it, and generalised from a sample of one.

Then I went back and did the others. Four companion apps, four successes:

| Companion app | Result |
|---|---|
| iLok License Manager | works — needs a patched installer |
| Native Access | works |
| Arturia Software Center | works |
| Slate Complete Access Hub | works — needs real PowerShell |

They are more work than a plugin that activates in its own window. They are not a wall.

**The replacement rule is about rendering, not licensing.** See the JUCE 8 section below — that's what actually decides whether a plugin is usable now.

Soundtoys note: the installer's last page warns that iLok License Manager is "needed even if no iLok device is used." Ignore it. The licensing layer installs either way; only the USB dongle driver fails, and that only matters if you own a dongle. Store the licence **on the computer**, not on an iLok.

---

# Cradle Hub: two separate problems

Cradle's plugins work fine once you're signed in. Getting signed in took a while.

### Blank window on launch

Cradle Hub starts, the process is alive, and you get an empty window. It's not Electron — it's their own engine — so none of the usual `--disable-gpu` flags apply.

Cause is Wine stubbing `DxgiOutput::WaitForVBlank`, the same call behind frozen plugin UIs further down this post. DXVK implements it.

**Install DXVK in a throwaway prefix for Cradle Hub, not in your DAW prefix.** DXVK is prefix-wide and you don't want to find out the hard way.

    WINEPREFIX=$HOME/.cradle-hub winetricks -q dxvk

The *plugins* don't need DXVK. Only the Hub window does.

### Sign-in that never completes

Click sign in, the browser opens, you authenticate, and then nothing. The Hub sits there unsigned-in forever.

It's a custom URL scheme handoff — the browser is supposed to hand the callback back to the app — and the handler isn't registered on Linux.

**The scheme is `app.cradle`, not `cradle`.** That's the whole problem. Everyone guesses the brand name.

I found it with F12 → Network, signing in, and reading the `303` response. The `location:` header was:

    location: app.cradle://oidc/cb?code=...

Register that exact string in three places:

1. A `.desktop` file with `MimeType=x-scheme-handler/app.cradle;` pointing at a script that launches the Hub
2. `xdg-mime default <your>.desktop x-scheme-handler/app.cradle`
3. Firefox's `network.protocol-handler.*` prefs, so it offers to open the app instead of silently dropping it

After that, signing in shows an "allow this site to open the application" prompt and completes.

**Generalisable version:** if any Wine app signs you in through your browser and the handoff silently fails, open devtools, catch the redirect, and read the `location:` header. The scheme is often not what the brand is called. Don't guess it.

---

# [edit 2] Companion apps: iLok, Native Access, Arturia, Slate

The pattern that worked for all four: **install the companion app in its own prefix, then symlink what the plugin needs into the DAW prefix.** Never install a companion app into your DAW prefix directly.

### iLok License Manager

This is the one I'd written off. The installer is a WiX Burn bundle, and four things have to change:

1. **Set the prefix to Windows 10.** `winetricks -q win10`. On its own this isn't enough.
2. **Get the MSI out of the bundle.** `/layout` and `7z` both failed for me. What worked was watching the package cache directory while the bundle runs and grabbing `LicenseSupport.msi` as it lands.
3. **Install with `/qb`, not `/qn`.** This is the actual gate. The MSI's `SetCompatibleOSVersion` custom action is conditioned on `UILevel <= 2`, and `/qn` *is* UILevel 2 — so fully silent installs skip the action that makes the version check pass. `/qb` runs at UILevel 3 and it fires. Pass `COMPATIBLE_OS_VERSION=True` as well.
4. **Empty the `Wix4ServiceConfig` table.** One row, and it calls `QueryServiceConfig2W` at a level Wine doesn't implement. `msiinfo export` it, blank it, `msibuild -i` it back.

You'll get a dialog about `iLokDrvr64.inf` failing. That's the USB dongle driver. Ignore it unless you own a physical iLok.

**The part I didn't expect: PACE fingerprints the hardware, not the prefix.** Activate a licence in the iLok prefix and a plugin in a *completely separate* prefix can see and use it. You still want the PACE layer installed in the DAW prefix, but the activation itself carries across.

### Real PowerShell, and the trap underneath it

Slate's Complete Access Hub shells out to PowerShell. Wine ships a stub that prints `fixme:powershell:wmain stub` and **exits 0** — so every check the installer runs appears to succeed and does nothing.

Drop a real PowerShell in and it works. But here's the part that cost me time: **a 32-bit installer asking for `C:\windows\system32\...` gets served `syswow64` instead.** WOW64 redirection. I tested PowerShell by hand, got `HELLO` back, and then watched the installer hit the stub anyway. Put the binary in **both** `system32` and `syswow64`.

### Arturia

Software Center and Pigments install into their own prefix with no special configuration, and the standalone renders fine. In FL, Pigments needs **Make bridged** and **External window** or the embedded editor goes transparent when you hover over it and shows whatever is behind the window. Which is the same `id 2` transplant from the Waves section, used for a completely different reason.

Arturia's download page offers a macOS `.pkg` and a Windows `.exe`. Take the `.exe`.

### Kontakt

Own prefix, symlink the library folders into FL's. One warning: **Waves and Native Instruments share the `Common Files\Native Instruments\Service Center` registration folder.** Symlinking that directory wholesale replaces your Waves licence files with NI's. Merge it per file instead. I caught this one about two seconds before it stuck.

`komplete.db3` is SQLite with WAL, so only one Kontakt instance can hold it. NTKDaemon serves over localhost, so one instance covers every prefix — a second one just exits.

---

# [edit 2] JUCE 8 blank windows — the actual blocker now

Soothe 3 installs, authorises through iLok, and processes audio. The editor is a blank window.

It's not iLok and it's not oeksound. **JUCE 8 renders through Direct2D on a composition swapchain**, which needs `CreateSwapChainForComposition` plus a set of DirectComposition calls. Wine implements neither. Neither does DXVK — I tested both ways: white window with DXVK, black without, same gap underneath.

There's no configuration that avoids this. The plugin has no renderer toggle, and the fix has to come from upstream in JUCE. Newer JUCE versions detect Wine and fall back; anything built before that doesn't.

**So the useful question before buying a plugin is no longer "does it need a manager app." It's "what did they build the UI with."** A JUCE 8 plugin from the last year or so is the risk case. Everything else in my working list draws fine.

If you own something affected, it's worth mailing the vendor — it's a JUCE version bump on their end and they may not know it affects anyone.

---

# Audio

Both of these took me months to track down, and neither is FL's fault.

### Input recorded garbled and pitched down

PipeWire's pro-audio profile was exposing my interface as four channels named `aux0..aux3`, and FL was grabbing all four. I'm on an Arturia MiniFuse 2, which is a 2-in interface.

    pactl list short sources

Fix is a remapped two-channel source:

    pactl load-module module-remap-source \
      source_name=iface_stereo \
      master=<the alsa_input... name from above> \
      channels=2 \
      master_channel_map=aux0,aux1 \
      channel_map=front-left,front-right

**Map from the real channel names.** Using `front-left,front-right` on a card that publishes `aux0..aux3` gives you a source that exists, appears in FL, and is completely silent. I lived with this one for a little under a year.

### Crackling and dropouts

Isolate it first — record the same input in Audacity or `arecord`. If that's clean, it's FL or Wine. If it crackles there too, it's PipeWire or CPU contention.

Then, in order of impact:

**1. Pin the quantum.** Single biggest fix:

    pw-metadata -n settings 0 clock.force-quantum 256

Dynamic quantum renegotiation and a Wine audio client don't get along. 512 if 256 still crackles, 128 if your machine can hold it. Resets on reboot, so put it in a launcher.

**2. CPU contention.** `pw-top -b -n 3` — watch the ERR column, that's xruns. Mine was a Windows VM I'd left running with most of my cores assigned to it.

**3. Realtime priority.** FL asks Windows to promote its audio threads and Wine stubs the call:

    fixme:avrt:AvSetMmThreadCharacteristicsW (L"Pro Audio",...): stub

So the request succeeds and does nothing. Check `ulimit -r` — if it prints 0, your user can't take realtime priority at all and setting up `rtprio` limits gives Wine something to work with. The stub is upstream though; nothing you configure in FL changes it.

### Latency, and why 60 ms doesn't kill it

FL's ASIO over Wine's WASAPI bottoms out around 60 ms round trip at a 512 buffer. WineASIO would help but its registration has been broken since Wine 10.2 and is unfixed.

In practice it's perfectly usable. The only place you notice is tracking vocals, where the monitor comes back delayed. I turn the playback volume down and record while listening to my own voice in the room. Keeps me on tempo and I still get a clean take. The latency affects what you hear back, not what gets recorded.

---

# Graphics — read this before blaming Wine for anything

I installed DXVK to fix a plugin with a frozen UI, FL got slower than it had been in a VM, and I concluded DXVK was poison for a DAW prefix. I was wrong, and I'd nearly published that as advice.

What was actually in the log:

    fixme:d3d:wined3d_guess_card No card selector available for card vendor 0000
      (using GL_RENDERER "llvmpipe (LLVM 19.1.7, 256 bits)")
    libEGL warning: egl: failed to create dri2 screen

`llvmpipe` is CPU rasterization. My GPU hadn't been doing anything for days, with or without DXVK.

`glxinfo -B` didn't just report software rendering, it failed outright:

    X Error of failed request: BadValue
      Major opcode: 149 (GLX)
      Minor opcode: 24 (X_GLXCreateNewContext)

And:

    Failed to initialize NVML: Driver/library version mismatch
    NVML library version: 620.70

An `apt upgrade` had moved the driver from 615 to 620 and I'd never rebooted. The kernel module in memory and the userspace libraries were different versions. NVML won't init, the Vulkan ICD won't load, GLX can't create a context, everything falls back to the CPU.

**Run these before theorising about anything:**

    nvidia-smi --query-gpu=driver_version --format=csv,noheader
    glxinfo -B | grep -i "OpenGL renderer"
    cat /proc/driver/nvidia/version

If the loaded module version differs from your packages, reboot — but **check the module is built for your running kernel first**, or you come back with no driver:

    /usr/sbin/dkms status
    uname -r

(`dkms` lives in `/usr/sbin`, which Debian leaves off a normal user's PATH. "command not found" means nothing.)

### DXVK, with a working GPU

Some plugins draw a window and then freeze on the first frame, repainting only when you minimise and restore. That's Wine stubbing `DxgiOutput::WaitForVBlank` — a vsync-driven render loop calls it, gets an error, and exits.

Launch FL from a terminal and grep the output for `WaitForVBlank` to confirm.

DXVK implements it. With a live GPU it fixed the frozen plugin and cost nothing in performance.

Caveats that still hold: DXVK is **prefix-wide**, so keep one prefix per app. And know how to remove it — note both spellings:

    for d in dxgi d3d8 d3d9 d3d10core d3d11; do
      wine reg delete "HKCU\Software\Wine\DllOverrides" /v "$d" /f 2>/dev/null
      wine reg delete "HKCU\Software\Wine\DllOverrides" /v "*$d" /f 2>/dev/null
    done
    wineserver -k

One gotcha: winetricks tracks installs in `$WINEPREFIX/winetricks.log` and never checks reality. If something restored Wine's builtin DLLs (`wineboot -u` will), winetricks still says "dxvk already installed, skipping". Delete that line from the log to force a reinstall.

---

# The "missing files" dialog is always blank

FL tells you "X sample(s) required by this project could not be located" above a completely empty list box. The selection highlight paints and the scrollbar is sized for real rows — only the text never appears. So you're told something is broken and never what. Same for the missing-plugins version of the dialog.

Reproduces on a fresh FL install in a fresh prefix. It is not your setup.

Not a colour problem (I tested by inverting `WindowText` — it blanks Wine's own file dialogs and leaves FL's list unchanged). The two buttons on the dialog just open image-line.com support pages. Can't be tested with `uxtheme=d` because FL won't start without it.

If anyone knows a fix for this I would love to hear it!

**Read the list out of the project file instead.** Plugin paths are plain ASCII, sample paths are UTF-16LE:

    strings yourproject.flp | grep -iE '\.(dll|vst3|clap)' | sort -u
    strings -el yourproject.flp | grep -iE '\.(wav|mp3|ogg|flac)' | sort -u
    strings    yourproject.flp | grep -iE '\.(wav|mp3|ogg|flac)' | sort -u

You get the full path FL expected, which is more than the dialog would have told you even if it worked.

Also worth knowing: FL records the plugin *format*. A project naming `Something.clap` will not load `Something.vst3`, so reinstalling in the wrong format looks like the reinstall failed.

### Zipped projects

FL opens zipped projects directly and under Wine that's a common source of phantom missing samples — they're in the archive, FL's temp extraction just doesn't resolve them. Extract it yourself and open the `.flp` from the extracted folder. FL checks the `.flp`'s own folder first.

---

# Don't do these

**`winetricks comctl32`** — on a modern wow64 prefix it installs a **Windows 98-era** DLL and deletes the Common-Controls 6.0 winsxs manifests. Afterwards every process throws `Could not find dependent assembly` and `winecfg` itself errors. Recovery means dropping the override, deleting the DLL, `wineboot -u`, and copying the manifests back from a clean prefix — `wineboot` alone doesn't restore them.

**`WINEDLLOVERRIDES="uxtheme=d"`** — FL won't start. `unimplemented function uxtheme.dll.GetWindowTheme`.

**`wineserver -k` without checking** — kills every process in the prefix instantly, including a render or save in progress, and takes `WavesLocalServer` with it. The same goes for anything that calls `wineserver -w`; winetricks does, and it'll hang forever waiting for FL to close.

---

# A few smaller ones

**Plugin windows forced to maximum size** — winecfg has "Emulate a virtual desktop" ticked. Untick it.

**FL rejects a sample folder path** — FL won't accept a bare drive root as a search path. Map the Wine drive one level higher and add a subfolder.

**Can't delete entries in FL's plugin manager** — white entries are FL's locked built-in defaults, orange are user-added. Only the orange ones are yours.

---

# Launcher script

Rather than remembering the PipeWire bits every session, and rather than going through Lutris:

    #!/bin/bash
    # ~/.local/bin/fl
    export WINEPREFIX="$HOME/flstudio"

    pactl list short sources | grep -q iface_stereo || \
      pactl load-module module-remap-source source_name=iface_stereo \
        master="<your alsa_input name>" channels=2 \
        master_channel_map=aux0,aux1 channel_map=front-left,front-right >/dev/null 2>&1

    pw-metadata -n settings 0 clock.force-quantum 256 >/dev/null 2>&1

    exec wine "$WINEPREFIX/drive_c/Program Files/Image-Line/FL Studio 2025/FL64.exe" "$@"

`chmod +x` and you launch with `fl`. Environment variables set before it pass through, which is handy for debugging — `WINEDEBUG=+text fl > /tmp/log 2>&1` and so on.

**[edit 2]** Once you have five prefixes, knowing which one is actually running stops being obvious. `examples/fl-aliases.sh` in the repo has a launcher per app plus a `wp` command that lists prefix state. One note if you build your own: `pgrep -f wineserver` does **not** tell you which prefix is live — wineserver's command line carries no prefix, so it reports everything idle including running ones. Read the socket instead:

    d=$(stat -c '%d' "$WINEPREFIX"); i=$(stat -c '%i' "$WINEPREFIX")
    [ -S "/tmp/.wine-$(id -u)/server-$(printf '%x' "$d")-$(printf '%x' "$i")/socket" ] \
      && echo LIVE || echo idle

---

# What I haven't tested

Being upfront so nobody wastes time assuming:

* Waves V14/V15/V16 — only V17 here
* Whether bridging solves Waves in other DAWs under Wine. Reaper, Bitwig and Ableton all have their own sandboxing or bridging — someone found Renoise's plugin sandboxing fixed WaveShell crashes on *Windows*, which is what put me onto this. If you try it, please reply.
* Whether the `id 2` layout holds across FL versions. If the record isn't 25 bytes for you the script skips the file rather than corrupting it.
* Whether automation on bridged Waves plugins behaves normally over a long session
* Whether any of it survives an FL update
* VST2 Waves — I'm on VST3 throughout
* **[edit 2]** The rest of the iLok catalogue. The licensing path is proven, but every plugin still has to clear the JUCE 8 problem separately.
* **[edit 2]** The rest of Komplete, the rest of Slate's Complete Access, and the rest of Arturia's V Collection. One plugin from each vendor works; I haven't bought the bundles.
* **[edit 2]** iZotope, reFX, UA and Spectrasonics. Their companion apps are the four I haven't tried.

---

# "Why not dual boot, or just use the VM, or use a native Linux DAW?"

**Why FL and not a Linux-native DAW:** FL's arrangement workflow is far more familiar to me than anything else, the interface is genuinely modern, and the stock plugins are more versatile than people give them credit for — I made everything with stock plugins and Vital for over a year. My whole catalogue is in FL projects and those don't port anywhere.

**Why not dual boot:** rebooting to make music means making less music. I do too much other stuff on this machine to be switching OSes for it.

**Why Linux at all:** it's faster than Windows for me, and I have complete control over what's on my PC. I can fix things from a terminal — including FL itself, which is literally what this whole post is. You don't get that on Windows, for pretty much anything.

And the VM is gone now. It existed purely as a one-time authoring step for Waves templates, and it isn't needed anymore.

---

# Is it worth it?

Absolutely! Audio is clean, latency is usable, everything animates. I tracked a full vocal chain with no issues, using plugins from Waves, Soundtoys, FabFilter and Cradle.

The honest summary: nothing here was hard once I knew the answer. The hard part was that almost none of it is online anywhere, and Wine's stderr — which nobody enjoys reading — was right every single time.

**[edit 2]** And the thing I'd most want someone else to take from this: the one rule in the original post that sounded the most useful was the one I'd tested least. I'd failed to install a single companion app and turned that into a law about all of them. Going back and actually testing the other four is what opened up Kontakt, Arturia and Slate. If something in here reads as a confident general rule, check how many cases it's standing on.

Everything is in the repo: [github.com/NuclearSurvivor/fl-studio-linux](https://github.com/NuclearSurvivor/fl-studio-linux)

Happy to answer questions.
