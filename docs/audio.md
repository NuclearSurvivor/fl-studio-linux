# Audio

Two problems, both of which took months to track down, and neither is FL's fault.

## Input recorded garbled and pitched down

PipeWire's pro-audio profile exposes some interfaces as four channels named
`aux0..aux3`, and FL grabs all four. On a 2-in interface (Arturia MiniFuse 2 here)
that means the recording is nonsense.

```bash
pactl list short sources
```

Fix is a remapped two-channel source:

```bash
pactl load-module module-remap-source \
  source_name=iface_stereo \
  master=<the alsa_input... name from above> \
  channels=2 \
  master_channel_map=aux0,aux1 \
  channel_map=front-left,front-right
```

**Map from the real channel names.** Using `front-left,front-right` as the
*master* map on a card that publishes `aux0..aux3` gives you a source that exists,
appears in FL, and is completely silent. That one cost a year.

## Crackling and dropouts

Isolate first — record the same input in Audacity or `arecord`. Clean there means
it's FL or Wine. Crackling there too means PipeWire or CPU contention.

Then, in order of impact:

### 1. Pin the quantum — the single biggest fix

```bash
pw-metadata -n settings 0 clock.force-quantum 256
```

Dynamic quantum renegotiation and a Wine audio client don't get along. 512 if 256
still crackles, 128 if the machine can hold it. Resets on reboot, so put it in a
launcher — see [`examples/fl`](../examples/fl).

### 2. CPU contention

```bash
pw-top -b -n 3
```

Watch the **ERR** column — those are xruns. A Windows VM left running with most
of the cores assigned to it was the culprit here.

### 3. Realtime priority

FL asks Windows to promote its audio threads and Wine stubs the call:

```
fixme:avrt:AvSetMmThreadCharacteristicsW (L"Pro Audio",...): stub
```

The request succeeds and does nothing. Check `ulimit -r` — if it prints 0 the user
can't take realtime priority at all, and setting up `rtprio` limits at least gives
Wine something to work with. The stub itself is upstream; no FL setting changes it.

## Latency

FL's ASIO over Wine's WASAPI bottoms out around **60 ms round trip at a 512
buffer**. WineASIO would cut most of that out but its registration has been broken
since Wine 10.2 and is unfixed.

In practice it's usable. The only place it bites is tracking vocals, where the
monitor comes back delayed. Turn playback down and record while listening to your
own voice in the room — the latency affects what you hear back, not what gets
recorded. Hardware monitoring on the interface solves it properly if you have it.

If low-latency live tracking is the main constraint, a native Linux DAW with
[yabridge](https://github.com/robbert-vdh/yabridge) is the better tool. This setup
trades latency for keeping FL.
