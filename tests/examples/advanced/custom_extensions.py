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
        freq_ctrl = self.add_floatbox(frequency, name=f"freq_{len(self._boxes)}")
        res_ctrl = self.add_floatbox(resonance, name=f"res_{len(self._boxes)}")
        filter_obj = self.add_textbox("biquad~ lowpass")

        # Connect controls
        self.add_line(freq_ctrl, filter_obj, outlet=0, inlet=1)
        self.add_line(res_ctrl, filter_obj, outlet=0, inlet=2)

        return filter_obj, freq_ctrl, res_ctrl

    def add_envelope_generator(self, attack=10, decay=100, sustain=0.3, release=500):
        """Add an ADSR envelope with controls."""
        a_ctrl = self.add_floatbox(attack, name=f"attack_{len(self._boxes)}")
        d_ctrl = self.add_floatbox(decay, name=f"decay_{len(self._boxes)}")
        s_ctrl = self.add_floatbox(sustain, name=f"sustain_{len(self._boxes)}")
        r_ctrl = self.add_floatbox(release, name=f"release_{len(self._boxes)}")

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

        # Create oscillators
        for i, freq in enumerate(frequencies):
            osc = self.add_textbox(f"cycle~ {freq}")
            gain = self.add_floatbox(amplitude, name=f"osc{i}_gain")
            mult = self.add_textbox("*~")

            self.add_line(osc, mult)
            self.add_line(gain, mult, outlet=0, inlet=1)

            oscillators.append(osc)
            gains.append(gain)

        # Create mixer
        mixer = self.add_textbox("+~")
        for i, gain in enumerate(gains):
            # Connect the *~ objects to mixer
            mult_obj = self._boxes[-len(gains) + i]  # Get corresponding *~ object
            self.add_line(mult_obj, mixer)

        return oscillators, gains, mixer

    def add_delay_line(self, delay_time=250, feedback=0.3, wet_mix=0.3):
        """Add a delay line with feedback and wet/dry mix."""
        # Controls
        time_ctrl = self.add_floatbox(delay_time, name=f"delay_time_{len(self._boxes)}")
        feedback_ctrl = self.add_floatbox(feedback, name=f"feedback_{len(self._boxes)}")
        mix_ctrl = self.add_floatbox(wet_mix, name=f"wet_mix_{len(self._boxes)}")

        # Processing objects
        delay = self.add_textbox("delay~")
        feedback_mult = self.add_textbox("*~")
        input_sum = self.add_textbox("+~")
        wet_dry = self.add_textbox("crossfade~")

        # Connect controls
        self.add_line(time_ctrl, delay)
        self.add_line(feedback_ctrl, feedback_mult, outlet=0, inlet=1)
        self.add_line(mix_ctrl, wet_dry, outlet=0, inlet=2)

        # Connect signal flow (setup for external input/output)
        self.add_line(input_sum, delay)
        self.add_line(delay, feedback_mult)
        self.add_line(feedback_mult, input_sum, outlet=0, inlet=1)  # feedback

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

    # Add envelope
    env, env_ctrls = p.add_envelope_generator(5, 50, 0.7, 200)
    p.add_line(env, filter_obj, outlet=0, inlet=3)  # Envelope to filter

    # Add delay
    delay_system = p.add_delay_line(375, 0.4, 0.25)

    # Connect to delay
    p.add_line(filter_obj, delay_system["input"])
    p.add_line(filter_obj, delay_system["output"], outlet=0, inlet=0)  # dry signal
    p.add_line(
        delay_system["input"], delay_system["output"], outlet=0, inlet=1
    )  # wet signal

    # Output
    output = p.add_textbox("ezdac~")
    p.add_line(delay_system["output"], output)

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
    p.add_line(voice1_env, voice1_filter, outlet=0, inlet=3)

    # Voice 2
    voice2_oscs, voice2_gains, voice2_mix = p.add_oscillator_bank([165, 330], 0.3)
    voice2_filter, v2_freq, v2_res = p.add_lowpass_filter(2000, 0.4)
    voice2_env, v2_env_ctrls = p.add_envelope_generator(12, 60, 0.5, 400)

    p.add_line(voice2_mix, voice2_filter)
    p.add_line(voice2_env, voice2_filter, outlet=0, inlet=3)

    # Mix voices
    voice_mixer = p.add_textbox("+~")
    p.add_line(voice1_filter, voice_mixer)
    p.add_line(voice2_filter, voice_mixer)

    # Global effects
    delay_fx = p.add_delay_line(500, 0.35, 0.4)
    p.add_line(voice_mixer, delay_fx["input"])
    p.add_line(voice_mixer, delay_fx["output"], outlet=0, inlet=0)

    # Master output
    master_gain = p.add_floatbox(0.6, name="master_volume")
    master_mult = p.add_textbox("*~")
    output = p.add_textbox("ezdac~")

    p.add_line(delay_fx["output"], master_mult)
    p.add_line(master_gain, master_mult, outlet=0, inlet=1)
    p.add_line(master_mult, output)

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
