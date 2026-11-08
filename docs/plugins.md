# Plugin compatibility

Everything here was tested on the setup in the [README](../README.md): Debian,
wine-staging 11.21 (wow64), FL Studio Producer Edition v25.2.3 build 5171,
64-bit, VST3 throughout.

**Status key**

| | meaning |
|---|---|
| ✅ | loaded, UI opens, audio processes, used in real work |
| ⚪ | installed and instantiates, not used heavily enough to vouch for |
| 🔧 | works, but needs the setup step noted |
| ❌ | confirmed broken here |
| ❓ | untested — see [the rule](#the-rule-that-predicts-everything) for the prediction |

---

## The rule that predicts everything

It isn't copy protection that breaks under Wine. **It's copy protection that
needs a separate companion application.**

Soundtoys and oeksound Soothe use the *same* licensing tech — PACE/iLok. Soundtoys
activates with a code typed into the plugin's own window, and it worked first try.
Soothe needs [iLok License Manager](https://www.ilok.com) running as a separate
app, and PACE's License Support installer aborts under Wine (the MSI reads the
prefix as Windows 8.1 regardless of what you set, and fails its launch conditions).

So before buying: **does it activate inside the plugin, or does it need a manager
app?** That predicts Wine behaviour better than price or publisher.

Known companion apps that are the blocker, not the plugin: iLok License Manager,
[Native Access](https://www.native-instruments.com),
[reFX Cloud](https://refx.com), iZotope Product Portal, UA Connect.

---

## ✅ Working

### Waves — 🔧 needs bridging

[waves.com](https://www.waves.com) · Waves V17, WaveShell1-VST3 16.7

**All 301 shell plugins load from the browser** once the database entries are
patched. See [waves.md](waves.md) for the full method and
[`waves-bridge.py`](../waves-bridge.py) for the tool.

Used in real work: CLA-2A, CLA-76, PuigTec EQP1A, RVox, RVerb, H-Delay,
MetaFlanger, Waves Tune Real-Time, MondoMod, MaxxVolume, Q6/Q10, Vocal Rider,
Bass Rider, PAZ Analyzer, S1 Stereo Imager, Sibilance.

Requires [`WavesLocalServer`](waves.md#waveslocalserver) running and the licence
activated on this machine.

### FabFilter — ✅ no setup needed

[fabfilter.com](https://www.fabfilter.com) · installs and runs with zero
configuration. Activation is in-plugin.

| Plugin | Status |
|---|---|
| Pro-Q 4 | ✅ |
| Pro-C 3 | ✅ |
| Pro-DS | ✅ |
| Pro-R 2 | ✅ |
| Pro-L 2 | ✅ |
| Pro-MB | ⚪ |
| Pro-G | ⚪ |
| Saturn 2 | ✅ |
| Timeless 3 | ⚪ |
| Volcano 3 | ⚪ |
| Simplon | ⚪ |

### Soundtoys — ✅ no setup needed

[soundtoys.com](https://www.soundtoys.com) · Soundtoys 5.5 bundle. Uses PACE, but
activates in-plugin with a code, so iLok License Manager is never needed.

> The installer's last page warns that iLok License Manager is "needed even if no
> iLok device is used." **Ignore it.** The licensing layer installs either way;
> only the USB dongle driver fails, and that only matters if you own a dongle.
> Store the licence **on the computer**, not on an iLok.

Decapitator ✅ · Crystallizer ✅ · EchoBoy ⚪ · EchoBoy Jr ⚪ · Tremolator ✅ ·
PanMan ⚪ · PhaseMistress ⚪ · FilterFreak 1 & 2 ⚪ · Devil-Loc ⚪ ·
Devil-Loc Deluxe ⚪ · Radiator ⚪ · Little Radiator ⚪ · Little AlterBoy ⚪ ·
MicroShift ⚪ · Little MicroShift ⚪ · PrimalTap ⚪ · Little PrimalTap ⚪ ·
Little Plate ⚪ · SuperPlate ⚪ · SpaceBlender ⚪ · Micro ⚪ · EffectRack ⚪ ·
Sie-Q ⚪ (free, and it is a Soundtoys plugin despite the name sounding like a Plugin Alliance one)

### Valhalla DSP — ✅ no setup needed

[valhalladsp.com](https://valhalladsp.com) · no activation server, no manager app.
About as Wine-friendly as commercial audio software gets.

ValhallaVintageVerb ✅ · ValhallaDelay ✅ · the free ones (Supermassive,
Freq Echo, Space Modulator) install the same way.

### Xfer Records — ✅ no setup needed

[xferrecords.com](https://xferrecords.com) · Serum 2 ✅ · Serum 2 FX ✅ ·
[OTT](https://xferrecords.com/freeware) (free) ✅

### Vital — ✅ no setup needed

[vital.audio](https://vital.audio) · Vital and Vital Pro ✅. Has a native Linux
build too, but the Windows VST3 runs fine in the Wine prefix alongside everything
else, which keeps one plugin path instead of two.

### Cradle — 🔧 needs the Hub sign-in fix

[cradle.app](https://cradle.app) · The plugins work normally once you're signed in.
Getting signed in needs two fixes — a DXVK install for the Hub window and a URL
scheme registration. Both are in [cradle.md](cradle.md).

The God Particle ✅ · The Spirit ✅ · The Prince ❓ (not owned yet)

### Native Instruments — 🔧 separate prefix + symlinks

[native-instruments.com](https://www.native-instruments.com) · Kontakt 8 Player ✅ ·
Komplete Start / Analog Dreams ✅

Installs into its own Wine prefix via
[selimbucher/native-instruments](https://github.com/selimbucher/native-instruments),
then the plugin and its content tree are linked into the DAW's prefix. Native Access
itself runs fine under Wine. Full method in [kontakt.md](kontakt.md).

Reaktor 6 Player, Guitar Rig and the rest of Komplete: untested, same pipeline.

### Image-Line stock — ✅

[image-line.com](https://www.image-line.com) · everything in the All Plugins
Edition works. FLEX, Harmor, Sytrus, Maximus, Gross Beat, Slicex, Ogun,
Soundgoodizer, the lot. A full record was made with nothing but stock plugins and
Vital before any of this.

---

## ❌ Not working

### oeksound Soothe 3

[oeksound.com](https://oeksound.com) · **Installs and activates fine.** The plugin
itself is not the problem.

Two separate failures:

1. **iLok License Manager won't install.** PACE's `LicenseSupport.msi` fails its
   `LaunchConditions` with exit 1603 — `COMPATIBLE_OS_VERSION = False`, because
   `VersionNT = 603` (Windows 8.1) no matter what `winecfg` reports.
2. **The UI is a transparent window.** Soothe's editor uses
   `DxgiFactory::CreateSwapChainForComposition`, which DXVK does not implement.
   Even with licensing solved, the window draws nothing.

Not owned here — this was tested with the demo. Untried: Wine 7.0 with `winetricks msxml3 gdiplus d3dx9 d3dx10 d3dx11` and
ILM 5.6.1, which some reports say works. If you get it, open an issue.

---

## ❓ Untested — expect trouble

All of these need a companion application, so the rule above predicts failure.
None have actually been tested here, so they're listed as unknown, not broken.

| Plugin | Vendor | Blocker |
|---|---|---|
| [Komplete / Massive X / Guitar Rig](https://www.native-instruments.com) | Native Instruments | Native Access |
| [Nexus 4](https://refx.com) | reFX | reFX Cloud |
| [Ozone / Neutron / RX](https://www.izotope.com) | iZotope | Product Portal |
| [UAD Spark / LA-2A / 1176](https://www.uaudio.com) | Universal Audio | UA Connect |
| [Virtual Mix Rack / FG-X / Fresh Air](https://slatedigital.com) | Slate Digital | Slate Connect |
| [Omnisphere / Trilian / Keyscape](https://www.spectrasonics.net) | Spectrasonics | own installer + challenge/response |
| [Melodyne](https://www.celemony.com) | Celemony | iLok License Manager |
| [Auto-Tune](https://www.antarestech.com) | Antares | iLok License Manager |
| [Plugin Alliance / Brainworx](https://www.plugin-alliance.com) | Plugin Alliance | Installation Manager |

One with reported community success worth trying before writing off:

- **Arturia Pigments** — [arturia.com](https://www.arturia.com) · reported working
  through [Bottles](https://usebottles.com). Arturia Software Center is the
  companion app, which is the usual blocker, but people have got round it.

If you get any of these running, **please open an issue** — this table exists to
stop other people repeating the same dead ends.

---

## Worth knowing: native Linux alternatives

Not everything needs Wine. If you're building a chain from scratch rather than
porting one, these are native and excellent:

- [Surge XT](https://surge-synthesizer.github.io) — synth
- [Vital](https://vital.audio) — synth, native build available
- [Dragonfly Reverb](https://michaelwillis.github.io/dragonfly-reverb/) — reverb
- [Airwindows](https://www.airwindows.com) — large free collection
- [LSP Plugins](https://lsp-plug.in) — broad utility set
- [Calf Studio Gear](https://calf-studio-gear.org) — broad utility set
- [x42 plugins](https://x42-plugins.com) — metering and utility

---

## Related projects

- [tillrd/waves-linux](https://github.com/tillrd/waves-linux) — Waves into a
  *native* Linux DAW via yabridge. Different approach to this repo, worth reading.
- [yabridge](https://github.com/robbert-vdh/yabridge) — the standard way to run
  Windows VST plugins in a native Linux host. Use this instead if your DAW is native.
- [DXVK](https://github.com/doitsujin/dxvk) — Direct3D over Vulkan, needed for
  several plugin UIs. See [graphics.md](graphics.md).
- [WineHQ](https://www.winehq.org) · [winetricks](https://github.com/Winetricks/winetricks)
