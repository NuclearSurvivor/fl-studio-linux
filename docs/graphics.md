# Graphics

**Read this before blaming Wine for anything.**

## Check the GPU is actually alive first

DXVK got installed here to fix a frozen plugin UI, FL got slower than it had been
in a VM, and the conclusion was "DXVK is poison for a DAW prefix." That was wrong.

What was actually in the log:

```
fixme:d3d:wined3d_guess_card No card selector available for card vendor 0000
  (using GL_RENDERER "llvmpipe (LLVM 19.1.7, 256 bits)")
libEGL warning: egl: failed to create dri2 screen
```

`llvmpipe` is CPU rasterization. The GPU hadn't done anything for days, with or
without DXVK.

`glxinfo -B` didn't just report software rendering, it failed outright:

```
X Error of failed request: BadValue
  Major opcode: 149 (GLX)
  Minor opcode: 24 (X_GLXCreateNewContext)
```

And:

```
Failed to initialize NVML: Driver/library version mismatch
NVML library version: 620.70
```

An `apt upgrade` had moved the NVIDIA driver from 615 to 620 with no reboot. The
kernel module in memory and the userspace libraries were different versions. NVML
won't init, the Vulkan ICD won't load, GLX can't create a context, everything
falls back to the CPU.

**Run these before theorising about anything:**

```bash
nvidia-smi --query-gpu=driver_version --format=csv,noheader
glxinfo -B | grep -i "OpenGL renderer"
cat /proc/driver/nvidia/version
```

If the loaded module version differs from your packages, reboot — but check the
module is built for your running kernel first, or you come back with no driver:

```bash
/usr/sbin/dkms status
uname -r
```

`dkms` lives in `/usr/sbin`, which Debian leaves off a normal user's PATH.
"command not found" means nothing.

## DXVK, with a working GPU

Some plugins draw a window then freeze on the first frame, repainting only when
you minimise and restore. That's Wine stubbing `DxgiOutput::WaitForVBlank` — a
vsync-driven render loop calls it, gets an error, and exits.

Launch FL from a terminal and grep stderr for `WaitForVBlank` to confirm.

[DXVK](https://github.com/doitsujin/dxvk) implements it. With a live GPU it fixed
the frozen plugin and cost nothing in performance.

Caveats:

- **DXVK is prefix-wide.** One prefix per app.
- Know how to remove it, and note **both spellings** — winetricks writes some
  overrides with a leading asterisk:

```bash
for d in dxgi d3d8 d3d9 d3d10core d3d11; do
  wine reg delete "HKCU\Software\Wine\DllOverrides" /v "$d"  /f 2>/dev/null
  wine reg delete "HKCU\Software\Wine\DllOverrides" /v "*$d" /f 2>/dev/null
done
wineserver -k
```

A `reg delete` on the unprefixed name reports success and changes nothing, so an
override can look gone while it's still live. Always `reg query` instead of
trusting a delete.

- winetricks tracks installs in `$WINEPREFIX/winetricks.log` and never checks
  reality. If something restored Wine's builtin DLLs (`wineboot -u` does), it
  still says "dxvk already installed, skipping". Delete that line from the log to
  force a reinstall.

## JUCE 8 blank windows

**This is the biggest remaining obstacle to running plugins under Wine, and it has
nothing to do with copy protection.**

[JUCE](https://juce.com) is the framework most audio plugins are built with. JUCE 8
switched to a **Direct2D** renderer on Windows, which needs
`IDXGIFactory2::CreateSwapChainForComposition` plus DirectComposition's
`CreateTargetForHwnd`, `SetContent` and `Commit`.

**Wine implements none of them, and neither does DXVK.** A JUCE 8 plugin therefore
draws a blank window — white, black or flickering depending on how the host
composites it — while licensing and audio work perfectly.

Tracked as:

- [Wine bug 57833 — JUCE 8 incompatibility](https://list.winehq.org/hyperkitty/list/wine-bugs@list.winehq.org/thread/IM5YOV2KJZK5LUMIO2DXR5YTJJ5KLOBY/)
- [Wine bug 60636 — dcomp: JUCE 8 plugins flicker](https://bugs.winehq.org/show_bug.cgi?id=60636)
- [wine-devel: "Is anyone working on dxgi/dcomp - specifically CreateSwapChainForComposition?"](https://list.winehq.org/hyperkitty/list/wine-devel@list.winehq.org/thread/LEBIPKPARJIBWI4XKDZH43Z36XITO4B7)
  — described there as drawing "blank white", and as a heavy lift nobody has finished

### The fix is upstream, in JUCE

JUCE now **defaults to software rendering when it detects it is running under Wine**
([discussion](https://forum.juce.com/t/juce8-direct2d-wine-yabridge/64298)). So the
fix exists — but it lands per plugin, when each vendor rebuilds against a current
JUCE. There is nothing to configure on your side.

### Diagnosing it

- UI blank, everything else fine → suspect JUCE 8
- **Removing DXVK doesn't help.** Tested: soothe3 draws white with DXVK and black
  without it. Wine's own `d3d11` has the same gap, so this is not a DXVK problem to
  route around.
- Plugin's own config files won't have a renderer toggle — checked for soothe3, it's
  version strings only

### What you can do

Ask the vendor to rebuild. It's a JUCE version bump on their side, and they may not
know. A short, specific mail naming the missing APIs and JUCE's Wine detection is
much more likely to land than a bug report saying "doesn't work on Linux."

An older version of the same plugin, built before JUCE 8, will usually render fine.

### Known affected

- **oeksound soothe3** (1.0.5, newest as of June 2026) — authorises through iLok and
  processes audio, editor won't draw

Not affected, for contrast: FabFilter, Soundtoys, Valhalla, Arturia, Native
Instruments, Waves. Different frameworks or older JUCE.

## What DXVK does not fix

`DxgiFactory::CreateSwapChainForComposition` is **not implemented by DXVK** — see
above. It's also not implemented by Wine, so there's no configuration that avoids
it.
