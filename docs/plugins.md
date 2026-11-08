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

## The two rules that predict everything

### 1. The renderer, not the copy protection

**A plugin built with JUCE 8 before JUCE added Wine detection draws a blank window.**
Licensing works, audio works, the editor is white or black. Wine implements neither
`CreateSwapChainForComposition` nor the DirectComposition calls JUCE 8 needs, and
neither does DXVK — so there is no configuration that avoids it.

This is now the main thing that stops a plugin being usable. Details and diagnosis:
[JUCE 8 blank windows](graphics.md#juce-8-blank-windows).

### 2. Companion apps are an obstacle, not a wall

The older rule was "it isn't copy protection that breaks under Wine, it's copy
protection that needs a separate companion application." That held until it was
actually tested. Four companion apps, four successes:

| Companion app | Status |
|---|---|
| iLok License Manager | works — [ilok.md](ilok.md) |
| Native Access | works — [kontakt.md](kontakt.md) |
| Arturia Software Center | works — [companion-apps.md](companion-apps.md#arturia-pigments) |
| Slate Complete Access Hub | works — [companion-apps.md](companion-apps.md#slate-digital-complete-access-hub) |

They take more work: a separate prefix, symlinks, sometimes a real PowerShell — and
if the installer is 32-bit, a copy of that PowerShell in `syswow64` as well, or WOW64
redirection hands it Wine's stub. But they are not the blocker they were assumed to
be. The general method is in [companion-apps.md](companion-apps.md).

Still untested: iZotope Product Portal, reFX Cloud, UA Connect, Spectrasonics.

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

### Arturia — 🔧 separate prefix + symlinks

[arturia.com](https://www.arturia.com) · Pigments 7.0.1 ✅

Installs into its own prefix along with Arturia Software Center; standalone renders
and plays with no configuration. Linked into the DAW it needs **Make bridged** and
**External window**, or the embedded editor goes transparent on hover and shows
whatever is behind it. Method in
[companion-apps.md](companion-apps.md#arturia-pigments).

Arturia's download page offers a macOS `.pkg` and a Windows `.exe`. Take the `.exe`.

### Slate Digital — 🔧 separate prefix + iLok

[slatedigital.com](https://slatedigital.com) · Fresh Air ✅

Complete Access Hub runs under Wine once real PowerShell is in place — including the
`syswow64` copy, because the installer is 32-bit and WOW64 redirection otherwise
serves it Wine's stub. Licensing is entirely iLok, so there is no registry to migrate
between prefixes. Fresh Air loads, renders and processes audio in FL.

Method in [companion-apps.md](companion-apps.md#slate-digital-complete-access-hub).
The rest of the Complete Access catalogue is untested but goes through these same two
mechanisms.

### iLok / PACE — 🔧 patched installer

[ilok.com](https://www.ilok.com) · iLok License Manager ✅

Installs and runs under Wine after four changes to the installer, and plugins in a
*separate* prefix can see its activations — PACE fingerprints hardware, not the
prefix. Full method in [ilok.md](ilok.md).

This unlocks the whole iLok catalogue for licensing. Whether a given plugin is then
*usable* depends on rule 1.

### Image-Line stock — ✅

[image-line.com](https://www.image-line.com) · everything in the All Plugins
Edition works. FLEX, Harmor, Sytrus, Maximus, Gross Beat, Slicex, Ogun,
Soundgoodizer, the lot. A full record was made with nothing but stock plugins and
Vital before any of this.

---

## ⚠️ Licensed but unusable

### oeksound Soothe 3

[oeksound.com](https://oeksound.com) · 1.0.5

**Installs, authorises through iLok, processes audio.** The editor draws a blank
window and that makes it unusable.

Cause is [JUCE 8](graphics.md#juce-8-blank-windows), not iLok and not oeksound. Tested
both with DXVK (white) and without (black) — Wine's own `d3d11` has the same gap. The
plugin's config file has no renderer toggle.

1.0.5 is the newest version (June 2026) and predates JUCE's Wine-detection fix, so
this needs a rebuild on oeksound's side. Worth mailing them: it's a JUCE version bump
and they may not know it affects anyone.

If you want soothe specifically, **soothe 2** predates JUCE 8 and should render.

---

## ❓ Untested — expect trouble

None of these have been tested here. Since four companion apps now work, read this
table as "unknown and probably more work," not "broken."

| Plugin | Vendor | Blocker |
|---|---|---|
| [Nexus 4](https://refx.com) | reFX | reFX Cloud |
| [Ozone / Neutron / RX](https://www.izotope.com) | iZotope | Product Portal |
| [UAD Spark / LA-2A / 1176](https://www.uaudio.com) | Universal Audio | UA Connect |
| [Omnisphere / Trilian / Keyscape](https://www.spectrasonics.net) | Spectrasonics | own installer + challenge/response |
| [Melodyne](https://www.celemony.com) | Celemony | iLok — now solved, worth trying |
| [Auto-Tune](https://www.antarestech.com) | Antares | iLok — now solved, worth trying |
| [Plugin Alliance / Brainworx](https://www.plugin-alliance.com) | Plugin Alliance | Installation Manager |

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
