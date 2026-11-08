# iLok License Manager under Wine

**It installs and it works.** PACE License Support and iLok License Manager both run
under Wine, sign in, and license plugins — including plugins loaded by a DAW in a
*different* Wine prefix.

This was the single biggest "confirmed not working" item in every Wine audio guide,
including an earlier version of this one. It isn't.

Tested with: PACE License Support 6.0.2.6879 (bundle 5.0.2), iLok License Manager,
wine-staging 11.21 (wow64), Debian, FL Studio 2025.

---

## The short version

```bash
# 1. fresh prefix, Windows 10
export WINEPREFIX=$HOME/.wine-ilok
wineboot -i
winetricks -q win10

# 2. run the bundle once — it installs Bonjour and the VC++ redists, then fails
wine ~/Downloads/LicenseSupport.exe

# 3. grab LicenseSupport.msi out of the package cache while it installs (see below)

# 4. empty the Wix4ServiceConfig table
msiinfo export LicenseSupport.msi Wix4ServiceConfig | head -3 | sed 's/$/\r/' \
  > /tmp/idt/Wix4ServiceConfig.idt
cp LicenseSupport.msi LicenseSupport-patched.msi
msibuild LicenseSupport-patched.msi -i /tmp/idt/Wix4ServiceConfig.idt

# 5. install the patched MSI with /qb and the property override
wine msiexec /i LicenseSupport-patched.msi /qb COMPATIBLE_OS_VERSION=True
```

Four non-obvious things in there. Each took a round of debugging.

---

## Why `/qb` and not `/qn`

The installer fails with `1603` at `LaunchConditions`. The condition is:

```
Installed Or (VersionNT64 >= 603 and COMPATIBLE_OS_VERSION="True")
```

`VersionNT64` is satisfied — but note that Wine reports **603** even with the prefix
set to Windows 10, so you're only clearing the `>= 603` half by luck. `winetricks -q
win10` is still worth doing: WiX's Burn bootstrapper does its own OS detection and
refuses earlier otherwise.

`COMPATIBLE_OS_VERSION` is a PACE property, and under Wine it evaluates `False`. It's
an uppercase public property so it can be set on the command line — **but** there's a
custom action that recomputes it:

```
CustomAction:          SetCompatibleOSVersion   type 65 (runScript)
InstallExecuteSequence: SetCompatibleOSVersion   condition "UILevel <= 2"   sequence 99
```

Sequence 99, immediately before `LaunchConditions` at 100. With `/qn` (`UILevel = 2`)
that custom action runs and overwrites whatever you passed.

`/qb` sets `UILevel = 3`. That fails the CA's condition *and* skips `InstallUISequence`
entirely, so your command-line value survives to evaluation:

```
Action ended: LaunchConditions. Return value 1.
Property(S): COMPATIBLE_OS_VERSION = True
```

**`/qn` is the quiet flag everyone reaches for, and it is precisely the mode that
defeats the fix.**

## Why the `Wix4ServiceConfig` table has to go

Past launch conditions, the install runs to completion — files written, services
installed, `StartServices` returns 1, shortcuts created — and then dies at
`InstallFinalize`:

```
err:msi:execute_script Execution of script 0 halted; action
  "[SchedServiceConfig\PACELicenseDServices\0\restart\restart\restart...]
   Wix4ExecServiceConfig_X86" returned 1603
err:msi:ITERATE_Actions Execution halted, action "InstallFinalize" returned 1603
```

That's WiX setting failure/recovery behaviour on the `PACELicenseDServices` service —
what Windows should do if it crashes. Wine doesn't implement it:

```
fixme:service:QueryServiceConfig2W Level 2 not implemented
```

So a complete, working install gets rolled back over a cosmetic step. The table has
exactly one row:

```
ServiceName            FirstFailure  SecondFailure  ThirdFailure  ResetPeriodInDays
PACELicenseDServices   restart       restart        restart       1
```

Empty it and `Wix4ExecServiceConfig_X86` has nothing to do:

```bash
mkdir -p /tmp/idt
cp -f LicenseSupport.msi LicenseSupport-patched.msi
msiinfo export LicenseSupport-patched.msi Wix4ServiceConfig | head -3 \
  | sed 's/$/\r/' > /tmp/idt/Wix4ServiceConfig.idt
msibuild LicenseSupport-patched.msi -i /tmp/idt/Wix4ServiceConfig.idt
msiinfo export LicenseSupport-patched.msi Wix4ServiceConfig   # header rows only
```

`.idt` files need CRLF, which is what the `sed` is for — `msiinfo export` writes LF.

## Getting the MSI out of the bundle

`LicenseSupport.exe` is a WiX Burn bundle. `7z` can't unpack it and `/layout` just
copies the bundle. The reliable way is to race the package cache, since Burn writes
the MSI there and deletes it on rollback:

```bash
D="$WINEPREFIX/drive_c/ProgramData/Package Cache"
mkdir -p "$D"
( for i in $(seq 1 600); do
    f=$(find "$D" -name 'LicenseSupport.msi' 2>/dev/null | head -1)
    [ -n "$f" ] && cp "$f" ./LicenseSupport.msi && break
    sleep 0.2
  done ) &
wine LicenseSupport.exe /quiet
wait
ls -lh LicenseSupport.msi      # ~126 MB
```

Run the bundle normally at least once first — Bonjour and both VC++ redists install
from it cleanly, and the patched MSI expects them.

## The driver error is harmless

During install you'll get:

```
ERROR: --install package's .inf file path does not exist:
C:\Program Files (x86)\Common Files\PACE\iLokDriverPackages\EV\iLokDrvr64.inf
```

Click OK. That's `iLokPnputil.bat` trying to install the USB dongle driver through
`pnputil.exe`, which Wine only stubs (`fixme:pnputil:wmain stub`). It matters only if
you own a physical iLok. Licences stored on the computer or in iLok Cloud are
unaffected.

## PACE fingerprints the machine, not the prefix

Install the patched MSI into **every prefix that needs it** — the one you run ILM
from, and your DAW's prefix so plugins can see activations:

```bash
WINEPREFIX=$HOME/Image-Line wine msiexec /i LicenseSupport-patched.msi /qb \
  COMPATIBLE_OS_VERSION=True
```

It's an ordinary MSI with no winetricks verbs, so this is far less invasive than
most installers. Back up `system.reg` and `user.reg` first anyway.

Both prefixes report the **same machine** to iLok — same name, same activation
count. Moving between them costs no activations. PACE is fingerprinting hardware.

## What you get

ILM opens, signs in, lists licences, and plugins in the DAW's prefix authorise
against activations held on the machine. Verified end to end: soothe3 loaded in FL
Studio, found its activation, and processed audio without any licensing complaint.

## What this does *not* fix

A licensed plugin still has to be able to draw. soothe3 authorises perfectly and then
renders a blank window — that's [the JUCE 8 problem](graphics.md#juce-8-blank-windows),
which is unrelated to iLok and affects plugins with no copy protection at all.

So the correct framing is: **iLok is solved; rendering is the remaining frontier.**

## Untested

- Physical iLok dongles (the driver doesn't install)
- iLok Cloud sessions
- Whether activations survive a Wine or hardware change
- Melodyne, Auto-Tune, Slate, Eventide and the rest of the iLok catalogue — all now
  worth trying, none tested here
