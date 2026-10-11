# Advanced Usage

This guide covers advanced py2max features for power users and complex use cases.

## Working with Subpatchers

Subpatchers allow you to create hierarchical patches with encapsulated functionality.

### Creating Subpatchers

``` python
from py2max import Patcher

# Create main patch
main = Patcher('main.maxpat')

# Create subpatcher; Max needs the "p" prefix
voice = main.add_subpatcher('p voice')
sub = voice.subpatcher

# Add objects to subpatcher; inlet/outlet carry signals too
inlet = sub.add_textbox('inlet')
filter_obj = sub.add_textbox('lores~ 1000 0.5')
env = sub.add_textbox('adsr~ 10 100 0.3 500')
vca = sub.add_textbox('*~')
outlet = sub.add_textbox('outlet')

# Connect subpatcher internals
sub.add_line(inlet, filter_obj)
sub.add_line(filter_obj, vca)
sub.add_line(env, vca, outlet=0, inlet=1)
sub.add_line(vca, outlet)

# Use the subpatcher box in the main patch
osc = main.add_textbox('cycle~ 440')
output = main.add_textbox('dac~')

main.add_line(osc, voice)
main.add_line(voice, output)

main.save()
```

### Nested Subpatchers

``` python
from py2max.core.common import Rect

# Create deeply nested structure
main = Patcher('complex.maxpat')

# Level 1 subpatcher
synth_box = main.add_subpatcher('p synthesizer')
synth = synth_box.subpatcher

# Level 2 subpatcher inside synth
bank_box = synth.add_subpatcher('p oscillator-bank')
oscillator_bank = bank_box.subpatcher

# Add objects to nested subpatcher. Max numbers outlets by x, so each
# outlet sits right of the previous one.
for i in range(4):
    osc = oscillator_bank.add_textbox(f'cycle~ {220 * (i + 1)}')
    out = oscillator_bank.add_textbox('outlet', patching_rect=Rect(48 + 100 * i, 300, 30, 30))
    oscillator_bank.add_line(osc, out)

# Mix the bank's outlets; signals into one inlet sum
mixer = synth.add_textbox('+~')
synth_out = synth.add_textbox('outlet')
for i in range(4):
    synth.add_line(bank_box, mixer, outlet=i, inlet=0)
synth.add_line(mixer, synth_out)

output = main.add_textbox('dac~')
main.add_line(synth_box, output)
```

### Encapsulating a Selection

`Patcher.encapsulate()` wraps a set of existing objects into a subpatcher, automatically generating `inlet` / `outlet` objects for any connections that cross the selection boundary and rewiring the parent through the new subpatcher box -- the same operation as selecting objects and choosing *Encapsulate* in Max.

``` python
p = Patcher('voice.maxpat')
freq = p.add_textbox('sig~ 440')
osc = p.add_textbox('cycle~')
gain = p.add_textbox('gain~')
dac = p.add_textbox('ezdac~')
p.add_line(freq, osc)
p.add_line(osc, gain)
p.add_line(gain, dac)

# Wrap the middle pair; the boundary wires become an inlet and an outlet.
sub_box = p.encapsulate([osc, gain], text='p dsp')
# Parent is now: sig~ -> p dsp -> ezdac~
```

Connections wholly inside the selection move into the subpatcher; connections wholly outside it are untouched. Ports are de-duplicated by source.

## Data Containers and Persistence

### Buffers and Tables

A `buffer~` holds audio, so a wavetable computed in Python goes into a WAV file beside the patch; `buffer~ <name> <file>` loads it when the patch opens. A `table` holds ints, here the semitone steps of a scale.

``` python
import math
import struct
import wave
from pathlib import Path


def write_wavetable(path, samples, rate=44100):
    """Write ``samples`` (floats in -1..1) as a mono 16-bit WAV file."""
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b''.join(struct.pack('<h', round(x * 32767)) for x in samples))


path = Path('wavetable-synth.maxpat')
p = Patcher(path)

# Wavetables: a buffer~ holds audio, so write each one as a WAV file
# beside the patch; buffer~ loads it when the patch opens.
size = 512
sine = [math.sin(2 * math.pi * i / size) for i in range(size)]
saw = [2 * (i / size) - 1 for i in range(size)]
for name, samples in (('sine_wave', sine), ('saw_wave', saw)):
    write_wavetable(path.with_name(f'{name}.wav'), samples)
    p.add_textbox(f'buffer~ {name} {name}.wav')

# A table holds ints: semitone offsets of a major scale, read by index
scale = p.add_table('scale', array=[0, 2, 4, 5, 7, 9, 11, 12])

# Step through the scale
metro = p.add_textbox('metro 250')
step = p.add_textbox('counter 0 7')
root = p.add_textbox('+ 60')
mtof = p.add_textbox('mtof')
p.add_line(metro, step)
p.add_line(step, scale)
p.add_line(scale, root)
p.add_line(root, mtof)

# Wavetable oscillator: phasor~ ramps 0-1 through each wave~ table
phasor = p.add_textbox('phasor~ 440')
sine_lookup = p.add_textbox('wave~ sine_wave')
saw_lookup = p.add_textbox('wave~ saw_wave')
p.add_line(mtof, phasor)
p.add_line(phasor, sine_lookup)
p.add_line(phasor, saw_lookup)

# selector~ 2: an int picks input 1 or 2 (0 is off)
wave_select = p.add_intparam('wave_select', initial=1)
selector = p.add_textbox('selector~ 2 1')
p.add_line(wave_select, selector)
p.add_line(sine_lookup, selector, outlet=0, inlet=1)
p.add_line(saw_lookup, selector, outlet=0, inlet=2)

# Output
level = p.add_textbox('*~ 0.2')
dac = p.add_textbox('ezdac~')
p.add_line(selector, level)
p.add_line(level, dac)
p.add_line(level, dac, inlet=1)

p.save()
```

### Collections for Sequences

``` python
p = Patcher('sequencer.maxpat')

# Create sequence data: index -> value
melody_sequence = {
    0: [60, 100, 250],  # note, velocity, duration
    1: [64, 90, 250],
    2: [67, 110, 500],
    3: [60, 80, 250],
    4: [69, 100, 750],
}

rhythm_sequence = {0: 'kick', 1: 'snare', 2: 'kick', 3: 'hihat', 4: 'kick'}

# Create collections; an int in the left inlet outputs that index's value
melody_lookup = p.add_coll('melody', dictionary=melody_sequence)
rhythm_lookup = p.add_coll('rhythm', dictionary=rhythm_sequence)

# Sequence player
metro = p.add_textbox('metro 500')
counter = p.add_textbox('counter 0 4')

# Melody player
note_unpack = p.add_textbox('unpack i i i')
mtof = p.add_textbox('mtof')
osc = p.add_textbox('cycle~')
level = p.add_textbox('*~ 0.2')
dac = p.add_textbox('ezdac~')

# Rhythm player
drums = p.add_textbox('select kick snare hihat')

# Connect sequencer
p.add_line(metro, counter)
p.add_line(counter, melody_lookup)
p.add_line(counter, rhythm_lookup)

# Melody chain
p.add_line(melody_lookup, note_unpack)
p.add_line(note_unpack, mtof, outlet=0, inlet=0)
p.add_line(mtof, osc)
p.add_line(osc, level)
p.add_line(level, dac)
p.add_line(level, dac, inlet=1)

# Rhythm chain: one outlet per drum name
p.add_line(rhythm_lookup, drums)

p.save()
```

### Dictionaries for Complex Data

``` python
p = Patcher('patch-state.maxpat')

params = ["frequency", "amplitude", "filter_freq", "resonance"]
patch_dict = p.add_dict("patch_state")

# Save and load the dictionary as JSON
p.add_line(p.add_message("export patch_state.json"), patch_dict)
p.add_line(p.add_message("import patch_state.json"), patch_dict)

# Recall: `get key` answers "key value" from outlet 1; route splits by key
recall = p.add_message(", ".join(f"get {param}" for param in params))
p.add_line(recall, patch_dict)
router = p.add_textbox("route " + " ".join(params))
p.add_line(patch_dict, router, outlet=1)

for i, param in enumerate(params):
    control = p.add_floatparam(param, initial=0.5)
    # Store: "set key value" writes the control's value into the dict
    store = p.add_textbox(f"prepend set {param}")
    p.add_line(control, store)
    p.add_line(store, patch_dict)
    # "set" updates the control without sending the value back
    update = p.add_textbox("prepend set")
    p.add_line(router, update, outlet=i)
    p.add_line(update, control)
```

## Advanced Connection Patterns

### Fan-out Connections

``` python
p = Patcher('fan-out.maxpat', layout="flow")

source = p.add_textbox('cycle~ 440')

# Connect one source to multiple destinations
destinations = []
for i in range(6):
    dest = p.add_textbox(f'svf~ {200 + i * 300} 0.5')
    destinations.append(dest)

    # Fan out from source
    p.add_line(source, dest)

# Collect all processed signals
collector = p.add_textbox('+~')
for dest in destinations:
    p.add_line(dest, collector, outlet=2)  # svf~ band-pass

p.optimize_layout()
p.save()
```

### Feedback Loops

``` python
p = Patcher('feedback-delay.maxpat')

# Input
input_obj = p.add_textbox('adc~')

# Delay line with feedback: tapin~/tapout~, since a signal loop
# through delay~ is not allowed
tapin = p.add_textbox('tapin~ 1000')
tapout = p.add_textbox('tapout~ 500')  # ms
feedback_gain = p.add_floatparam('feedback', initial=0.3)
feedback_mult = p.add_textbox('*~')
input_mix = p.add_textbox('+~')

# Create feedback loop
p.add_line(input_obj, input_mix)
p.add_line(input_mix, tapin)
p.add_line(tapin, tapout)
p.add_line(tapout, feedback_mult)
p.add_line(feedback_gain, feedback_mult, outlet=0, inlet=1)
p.add_line(feedback_mult, input_mix, outlet=0, inlet=1)  # Feedback

# Output
output = p.add_textbox('dac~')
p.add_line(tapout, output)

p.save()
```

### Matrix Routing

A matrix mixer as an abstraction: a patcher file used as an object by its file name. Its `inlet` and `outlet` objects become the object's ports, numbered left to right by x.

``` python
from py2max import Patcher
from py2max.core.common import Rect


def create_matrix_mixer(n=4):
    """Create an n x n matrix mixer abstraction, ``matrix-mixer.maxpat``.

    Inlets 1-n take signals, inlet n+1 takes ``src dst gain`` messages
    (0-based indices); outlets 1-n carry the mixes. Gains start as the
    identity, so each input passes to the matching output.
    """
    p = Patcher("matrix-mixer.maxpat")
    col = 120  # x spacing; Max numbers inlets and outlets by x

    def rect(x, y, w=60.0):
        return Rect(x, y, w, 22.0)

    # Signal inlets and the control inlet, left to right
    inlets = [
        p.add_textbox("inlet", patching_rect=rect(40 + col * i, 20, 30))
        for i in range(n)
    ]
    control = p.add_textbox("inlet", patching_rect=rect(40 + col * n, 20, 30))

    # "src dst gain": route by src, then by dst, leaving the gain
    indices = " ".join(str(i) for i in range(n))
    by_src = p.add_textbox(
        f"route {indices}", patching_rect=rect(40 + col * n, 60, 100)
    )
    p.add_line(control, by_src)

    # Gain matrix: one *~ per (src, dst), in a column per source
    mults = {}
    for src in range(n):
        by_dst = p.add_textbox(
            f"route {indices}", patching_rect=rect(40 + col * n, 100 + 30 * src, 100)
        )
        p.add_line(by_src, by_dst, outlet=src)
        for dst in range(n):
            gain = 1.0 if src == dst else 0.0
            mult = p.add_textbox(
                f"*~ {gain}", patching_rect=rect(40 + col * src, 100 + 40 * dst)
            )
            p.add_line(inlets[src], mult)
            p.add_line(by_dst, mult, outlet=dst, inlet=1)
            mults[src, dst] = mult

    # Sum each destination's column of gains into its outlet
    for dst in range(n):
        summer = p.add_textbox("+~", patching_rect=rect(40 + col * dst, 120 + 40 * n))
        outlet = p.add_textbox(
            "outlet", patching_rect=rect(40 + col * dst, 160 + 40 * n, 30)
        )
        for src in range(n):
            p.add_line(mults[src, dst], summer)
        p.add_line(summer, outlet)

    p.save()
    return p


def create_matrix_mixer_host(n=4):
    """Use the ``matrix-mixer`` abstraction; save it beside this patch."""
    create_matrix_mixer(n)
    p = Patcher("matrix-mixer-host.maxpat")

    # An abstraction is an object named after its file. py2max cannot read
    # its port counts, so state them.
    mixer = p.add_textbox("matrix-mixer", numinlets=n + 1, numoutlets=n)
    channels = " ".join(str(i + 1) for i in range(n))
    dac = p.add_textbox(f"dac~ {channels}")

    for i in range(n):
        osc = p.add_textbox(f"cycle~ {220 * (i + 1)}")
        p.add_line(osc, mixer, inlet=i)
        p.add_line(mixer, dac, outlet=i, inlet=i)

    # Send source 0 to destination 1 at half gain
    msg = p.add_message("0 1 0.5")
    p.add_line(msg, mixer, inlet=n)

    p.optimize_layout()
    p.save()
    return p


create_matrix_mixer_host()
```

## Error Handling and Robustness

### Comprehensive Error Handling

``` python
from py2max import Patcher, InvalidConnectionError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_robust_patch(filename):
    try:
        p = Patcher(filename, validate_connections=True)

        # Track objects for cleanup on error
        created_objects = []

        try:
            # Create objects with error checking
            osc = p.add_textbox('cycle~ 440')
            created_objects.append(osc)

            gain = p.add_textbox('gain~')
            created_objects.append(gain)

            output = p.add_textbox('ezdac~')
            created_objects.append(output)

            # Attempt connections with validation
            p.add_line(osc, gain)
            logger.info("Connected oscillator to gain")

            p.add_line(gain, output)
            logger.info("Connected gain to output")

            # Validate object capabilities
            logger.info(f"Oscillator outlets: {osc.get_outlet_count()}")
            logger.info(f"Gain inlets: {gain.get_inlet_count()}")

            p.save()
            logger.info(f"Successfully created patch: {filename}")
            return p

        except InvalidConnectionError as e:
            logger.error(f"Connection error: {e}")
            # Could implement recovery logic here
            raise

        except Exception as e:
            logger.error(f"Unexpected error creating objects: {e}")
            # Cleanup logic could go here
            raise

    except Exception as e:
        logger.error(f"Failed to create patch {filename}: {e}")
        return None

# Use robust patch creation
patch = create_robust_patch('robust-patch.maxpat')
```

### Validation and Testing

``` python
def validate_patch_structure(patcher):
    """Validate patch structure and connections."""
    errors = []
    warnings = []

    # Check for disconnected objects
    connected_objects = set()
    for line in patcher._lines:
        connected_objects.add(line.src)
        connected_objects.add(line.dst)

    all_objects = set(obj.id for obj in patcher._boxes if obj.id)
    disconnected = all_objects - connected_objects

    if disconnected:
        warnings.append(f"Disconnected objects: {disconnected}")

    # Check for impossible connections
    for line in patcher._lines:
        try:
            src_obj = patcher._objects[line.src]
            dst_obj = patcher._objects[line.dst]

            src_outlets = src_obj.get_outlet_count()
            dst_inlets = dst_obj.get_inlet_count()

            if hasattr(line, 'outlet') and line.outlet >= src_outlets:
                errors.append(f"Invalid outlet {line.outlet} on {src_obj.maxclass}")

            if hasattr(line, 'inlet') and line.inlet >= dst_inlets:
                errors.append(f"Invalid inlet {line.inlet} on {dst_obj.maxclass}")

        except Exception as e:
            errors.append(f"Error validating connection: {e}")

    return errors, warnings

# Use validation
errors, warnings = validate_patch_structure(p)
if errors:
    print(f"Patch errors: {errors}")
if warnings:
    print(f"Patch warnings: {warnings}")
```

## Performance Optimization

### Large Patch Optimization

``` python
def create_large_patch_efficiently():
    """Create large patches with performance optimizations."""

    # Disable clustering for large patches if speed is critical
    p = Patcher('large-patch.maxpat',
               layout="grid",
               cluster_connected=False,  # Faster for 100+ objects
               validate_connections=False)  # Skip validation for speed

    # Batch object creation
    objects = []
    for i in range(200):
        obj = p.add_textbox(f'cycle~ {220 + i}')
        objects.append(obj)

    # Batch connection creation
    for i in range(0, len(objects) - 1, 2):
        p.add_line(objects[i], objects[i + 1])

    # Single layout optimization at the end
    p.optimize_layout()

    return p
```

### Memory Management

``` python
def process_many_patches(patch_configs):
    """Process multiple patches with memory management."""

    for config in patch_configs:
        # Create patch
        p = Patcher(config['filename'])

        # Add objects based on config
        for obj_config in config['objects']:
            p.add_textbox(obj_config['text'])

        # Process and save
        p.optimize_layout()
        p.save()

        # Explicit cleanup for large numbers of patches
        del p
```

## Custom Extensions

### Custom Object Creation

``` python
class CustomPatcher(Patcher):
    """Extended patcher with custom object creation methods."""

    def add_lowpass_filter(self, frequency=1000, resonance=0.707):
        """Add a lowpass filter with controls."""
        freq_ctrl = self.add_floatparam(f'freq_{len(self._boxes)}', initial=frequency)
        res_ctrl = self.add_floatparam(f'res_{len(self._boxes)}', initial=resonance)
        # lores~ inlets: signal, cutoff frequency, resonance (0-1)
        filter_obj = self.add_textbox(f'lores~ {frequency} {resonance}')

        # Connect controls
        self.add_line(freq_ctrl, filter_obj, outlet=0, inlet=1)
        self.add_line(res_ctrl, filter_obj, outlet=0, inlet=2)

        return filter_obj, freq_ctrl, res_ctrl

    def add_envelope_generator(self, attack=10, decay=100, sustain=0.3, release=500):
        """Add an ADSR envelope with controls."""
        a_ctrl = self.add_floatparam(f'attack_{len(self._boxes)}', initial=attack)
        d_ctrl = self.add_floatparam(f'decay_{len(self._boxes)}', initial=decay)
        s_ctrl = self.add_floatparam(f'sustain_{len(self._boxes)}', initial=sustain)
        r_ctrl = self.add_floatparam(f'release_{len(self._boxes)}', initial=release)

        env = self.add_textbox('adsr~')

        # Connect controls
        self.add_line(a_ctrl, env, outlet=0, inlet=1)
        self.add_line(d_ctrl, env, outlet=0, inlet=2)
        self.add_line(s_ctrl, env, outlet=0, inlet=3)
        self.add_line(r_ctrl, env, outlet=0, inlet=4)

        return env, (a_ctrl, d_ctrl, s_ctrl, r_ctrl)

    def add_gate(self, envelope):
        """Add [1( and [0( to gate ``envelope``: note-on and note-off."""
        note_on = self.add_message('1')
        note_off = self.add_message('0')
        self.add_line(note_on, envelope)
        self.add_line(note_off, envelope)
        return note_on, note_off

    def add_vca(self, signal, envelope):
        """Scale ``signal`` by ``envelope``; returns the ``*~``."""
        vca = self.add_textbox('*~')
        self.add_line(signal, vca)
        self.add_line(envelope, vca, outlet=0, inlet=1)
        return vca

# Use custom patcher
p = CustomPatcher('custom-synth.maxpat')

osc = p.add_textbox('cycle~ 440')
filter_obj, freq_ctrl, res_ctrl = p.add_lowpass_filter(2000, 0.5)
env, env_ctrls = p.add_envelope_generator(5, 50, 0.7, 200)

p.add_line(osc, filter_obj)
vca = p.add_vca(filter_obj, env)  # envelope scales the filtered signal

# Gate the envelope: non-zero starts the attack, 0 the release
p.add_gate(env)

p.save()
```

## Parameters and Presets

Objects participate in Max presets when they are parameter-enabled or bound to the `pattr` system. py2max provides scaffolding for both.

``` python
p = Patcher('device.maxpat')

# Turn an existing UI object into an automatable parameter.
tog = p.add_textbox('toggle', varname='mute')
p.enable_parameter(tog, 'Mute', ptype=1)        # ptype: 0=float 1=int 2=enum

# Add a complete preset system: autopattr + pattrstorage, connected.
autopattr, storage = p.add_preset_system('presets')

# Or add the objects individually.
p.add_autopattr()
p.add_pattrstorage('mypresets')

p.save()
```

Any object with a scripting name (`varname`) or `parameter_enable=1` participates in `pattrstorage` presets and, in a Max for Live device, appears as an automatable parameter.

## Multichannel (mc.) and Polyphony

``` python
p = Patcher('mc.maxpat')

# add_mc prefixes 'mc.' and appends @chans.
osc = p.add_mc('cycle~ 440', chans=4)   # -> "mc.cycle~ 440 @chans 4"
out = p.add_mc('live.gain~')
p.add_line(osc, out)                     # one cable carries all channels

# poly~ hosts N voices of a target patch.
voices = p.add_poly('mysynth', 8)        # -> "poly~ mysynth 8"

p.save()
```

## Gen Codebox DSP

`add_gen_codebox()` adds a standalone `gen.codebox~` object: a complete gen patch expressed as DSP code in a single box, sitting directly in a regular Max patcher. This is distinct from `add_codebox()`, which emits the inner `codebox~` object meant to live inside a `gen~`/`rnbo~` subpatcher. The whole feedback-delay built from discrete objects in [Feedback Loops](#feedback-loops) collapses into one box:

``` python
p = Patcher('fbdelay.maxpat')

osc = p.add('cycle~ 440')

# Inlet/outlet counts are derived from the highest inN/outN in the code:
# this references in1 and out1, so the box gets 1 signal inlet and 1 outlet.
cb = p.add_gen_codebox('''
Param feedback(0.5, min=0.0, max=0.95);
History fb(0.0);
out1 = in1 + fb * feedback;
fb = out1;
''')

dac = p.add('ezdac~')
p.add_line(osc, cb)
p.add_line(cb, dac)
p.save()
```

Pass `numinlets` / `numoutlets` explicitly to override the derived counts. Newlines in the code are normalized to CRLF as Max expects, and the font defaults to the monospaced gen style.

The box is sized to show all of the code: its height follows the line count, its width the longest line, both scaled by `fontsize`. `add_codebox()` and `add('codebox~', code=...)` size the inner codebox the same way. Pass `patching_rect` to set the size yourself.

For short, single-line code the `add()` string shortcut works too:

``` python
cb = p.add('gen.codebox~ out1 = in1 * 0.5;')
```

When `validate_connections=True`, connections to and from a `gen.codebox~` (and `codebox` / `codebox~`) are bound-checked against the box's own declared inlet/outlet counts rather than a fixed maxref entry, since codebox I/O is code-dependent.

## Colors and Theming

Boxes accept a named color, a hex string, or an `[r, g, b(, a)]` float sequence (0..1). `apply_theme` colors every box at once.

``` python
p = Patcher('themed.maxpat')

tog = p.add_textbox('toggle').set_color(bg='blue', text='white')
dial = p.add_textbox('live.dial').set_color(bg='#202020', border='#808080')

# Apply a built-in theme to every box (recurses into subpatchers).
p.apply_theme('dark')   # 'light' | 'dark' | 'blue' | 'high-contrast'
# ...or a custom theme dict:
p.apply_theme({'bg': 'black', 'text': 'yellow', 'border': 'yellow'})

p.save()
```

The named palette and `resolve_color` helper are in `py2max.core.colors`.

## Catching Attribute Typos

py2max warns when an object is given a property that is not a known attribute of its Max class.

``` python
p = Patcher('checked.maxpat')
p.add_floatparam('master', inital=0.5)        # typo for 'initial'
# -> UserWarning: Unknown attribute 'inital' for Max object 'flonum'
p.add_textbox('waveform~ @bufername buf')     # typo in text
# -> UserWarning: Unknown attribute 'bufername' for Max object 'waveform~'
```

Known attributes are the object's maxref attributes plus keys Max saves on every box. The check is warn-only, so it never changes generated output. Objects with no maxref entry are skipped. `Patcher(validate_attrs=False)` turns off the check for keywords; `@attr` names in text are still checked, because the type checker cannot see them.

This covers the advanced features of py2max for sophisticated patch creation and management.
