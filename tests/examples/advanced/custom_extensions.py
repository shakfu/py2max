#!/usr/bin/env python3
"""
Advanced Usage: Custom Extensions
==================================

Examples demonstrating custom patcher extensions and object creation methods.

This example is used in:
- docs/source/user_guide/advanced_usage.rst
"""

from py2max import Patcher


class CustomPatcher(Patcher):
    """Extended patcher with custom object creation methods."""

    def add_lowpass_filter(self, frequency=1000, resonance=0.707):
        """Add a lowpass filter with controls."""
        freq_ctrl = self.add_floatparam(f"freq_{len(self._boxes)}", initial=frequency)
        res_ctrl = self.add_floatparam(f"res_{len(self._boxes)}", initial=resonance)
        # lores~ inlets: signal, cutoff frequency, resonance (0-1)
        filter_obj = self.add_textbox(f"lores~ {frequency} {resonance}")

        # Connect controls
        self.add_line(freq_ctrl, filter_obj, outlet=0, inlet=1)
        self.add_line(res_ctrl, filter_obj, outlet=0, inlet=2)

        return filter_obj, freq_ctrl, res_ctrl

    def add_envelope_generator(self, attack=10, decay=100, sustain=0.3, release=500):
        """Add an ADSR envelope with controls."""
        a_ctrl = self.add_floatparam(f"attack_{len(self._boxes)}", initial=attack)
        d_ctrl = self.add_floatparam(f"decay_{len(self._boxes)}", initial=decay)
        s_ctrl = self.add_floatparam(f"sustain_{len(self._boxes)}", initial=sustain)
        r_ctrl = self.add_floatparam(f"release_{len(self._boxes)}", initial=release)

        env = self.add_textbox("adsr~")

        # Connect controls
        self.add_line(a_ctrl, env, outlet=0, inlet=1)
        self.add_line(d_ctrl, env, outlet=0, inlet=2)
        self.add_line(s_ctrl, env, outlet=0, inlet=3)
        self.add_line(r_ctrl, env, outlet=0, inlet=4)

        return env, (a_ctrl, d_ctrl, s_ctrl, r_ctrl)

    def add_oscillator_bank(self, frequencies, amplitude=0.25):
        """Add a bank of oscillators with mixer."""
        oscillators = []
        gains = []
        mults = []

        # Create oscillators
        for i, freq in enumerate(frequencies):
            osc = self.add_textbox(f"cycle~ {freq}")
            gain = self.add_floatparam(f"osc{i}_gain", initial=amplitude)
            mult = self.add_textbox("*~")

            self.add_line(osc, mult)
            self.add_line(gain, mult, outlet=0, inlet=1)

            oscillators.append(osc)
            gains.append(gain)
            mults.append(mult)

        # Create mixer: signals into one inlet sum
        mixer = self.add_textbox("+~")
        for mult in mults:
            self.add_line(mult, mixer)

        return oscillators, gains, mixer

    def add_gate(self, envelope):
        """Add [1( and [0( to gate ``envelope``: note-on and note-off."""
        note_on = self.add_message("1")
        note_off = self.add_message("0")
        self.add_line(note_on, envelope)
        self.add_line(note_off, envelope)
        return note_on, note_off

    def add_vca(self, signal, envelope):
        """Scale ``signal`` by ``envelope``; returns the ``*~``."""
        vca = self.add_textbox("*~")
        self.add_line(signal, vca)
        self.add_line(envelope, vca, outlet=0, inlet=1)
        return vca

    def add_delay_line(self, delay_time=250, feedback=0.3, wet_mix=0.3):
        """Add a delay line with feedback and wet/dry mix.

        Send the dry signal into ``input``; ``output`` carries the mix.
        """
        # Controls
        time_ctrl = self.add_floatparam(
            f"delay_time_{len(self._boxes)}", initial=delay_time
        )
        feedback_ctrl = self.add_floatparam(
            f"feedback_{len(self._boxes)}", initial=feedback
        )
        mix_ctrl = self.add_floatparam(f"wet_mix_{len(self._boxes)}", initial=wet_mix)

        # Processing objects: tapin~/tapout~, since a signal loop through
        # delay~ is not allowed
        input_sum = self.add_textbox("+~")
        tapin = self.add_textbox("tapin~ 2000")
        tapout = self.add_textbox(f"tapout~ {delay_time}")
        feedback_mult = self.add_textbox("*~")
        # wet * mix + dry * (1 - mix)
        dry_level = self.add_textbox("!- 1.")
        wet_gain = self.add_textbox("*~")
        dry_gain = self.add_textbox("*~")
        wet_dry = self.add_textbox("+~")

        # Connect controls
        self.add_line(time_ctrl, tapout)  # delay time in ms
        self.add_line(feedback_ctrl, feedback_mult, outlet=0, inlet=1)
        self.add_line(mix_ctrl, wet_gain, outlet=0, inlet=1)
        self.add_line(mix_ctrl, dry_level)
        self.add_line(dry_level, dry_gain, outlet=0, inlet=1)

        # Connect signal flow
        self.add_line(input_sum, tapin)
        self.add_line(tapin, tapout)
        self.add_line(tapout, feedback_mult)
        self.add_line(feedback_mult, input_sum, outlet=0, inlet=1)  # feedback
        self.add_line(tapout, wet_gain)
        self.add_line(input_sum, dry_gain)
        self.add_line(wet_gain, wet_dry)
        self.add_line(dry_gain, wet_dry, outlet=0, inlet=1)

        return {
            "input": input_sum,
            "output": wet_dry,
            "controls": {"time": time_ctrl, "feedback": feedback_ctrl, "mix": mix_ctrl},
        }


def create_custom_synthesizer():
    """Create a synthesizer using custom patcher methods."""
    # Use custom patcher
    p = CustomPatcher("custom-synth.maxpat")

    # Create oscillator bank
    frequencies = [220, 330, 440, 550]
    oscillators, osc_gains, osc_mixer = p.add_oscillator_bank(frequencies, 0.2)

    # Add filter
    filter_obj, freq_ctrl, res_ctrl = p.add_lowpass_filter(2000, 0.5)
    p.add_line(osc_mixer, filter_obj)

    # Add envelope, scaling the filtered signal
    env, env_ctrls = p.add_envelope_generator(5, 50, 0.7, 200)
    vca = p.add_vca(filter_obj, env)

    # Gate the envelope: non-zero starts the attack, 0 the release
    p.add_gate(env)

    # Add delay
    delay_system = p.add_delay_line(375, 0.4, 0.25)
    p.add_line(vca, delay_system["input"])

    # Output
    output = p.add_textbox("ezdac~")
    p.add_line(delay_system["output"], output)
    p.add_line(delay_system["output"], output, outlet=0, inlet=1)

    p.optimize_layout()
    p.save()

    return p


def create_modular_system():
    """Create a modular synthesizer system."""
    p = CustomPatcher("modular-system.maxpat")

    # Voice 1
    voice1_oscs, voice1_gains, voice1_mix = p.add_oscillator_bank([110, 220], 0.3)
    voice1_filter, v1_freq, v1_res = p.add_lowpass_filter(1500, 0.6)
    voice1_env, v1_env_ctrls = p.add_envelope_generator(8, 80, 0.6, 300)

    p.add_line(voice1_mix, voice1_filter)
    voice1_vca = p.add_vca(voice1_filter, voice1_env)
    p.add_gate(voice1_env)

    # Voice 2
    voice2_oscs, voice2_gains, voice2_mix = p.add_oscillator_bank([165, 330], 0.3)
    voice2_filter, v2_freq, v2_res = p.add_lowpass_filter(2000, 0.4)
    voice2_env, v2_env_ctrls = p.add_envelope_generator(12, 60, 0.5, 400)

    p.add_line(voice2_mix, voice2_filter)
    voice2_vca = p.add_vca(voice2_filter, voice2_env)
    p.add_gate(voice2_env)

    # Mix voices
    voice_mixer = p.add_textbox("+~")
    p.add_line(voice1_vca, voice_mixer)
    p.add_line(voice2_vca, voice_mixer)

    # Global effects
    delay_fx = p.add_delay_line(500, 0.35, 0.4)
    p.add_line(voice_mixer, delay_fx["input"])

    # Master output
    master_gain = p.add_floatparam("master_volume", initial=0.6)
    master_mult = p.add_textbox("*~")
    output = p.add_textbox("ezdac~")

    p.add_line(delay_fx["output"], master_mult)
    p.add_line(master_gain, master_mult, outlet=0, inlet=1)
    p.add_line(master_mult, output)
    p.add_line(master_mult, output, outlet=0, inlet=1)

    p.optimize_layout()
    p.save()

    return p


if __name__ == "__main__":
    # Create custom synthesizer
    custom_synth = create_custom_synthesizer()
    print(f"Created custom synthesizer with {len(custom_synth._boxes)} objects")

    # Create modular system
    modular_system = create_modular_system()
    print(f"Created modular system with {len(modular_system._boxes)} objects")
