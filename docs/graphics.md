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

## What DXVK does not fix

`DxgiFactory::CreateSwapChainForComposition` is **not implemented by DXVK**. Any
plugin whose editor uses Direct2D composition draws a transparent window and no
amount of configuration helps. oeksound Soothe 3 is the known case here.
