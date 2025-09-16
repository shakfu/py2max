

CONTROL_OBJECTS = {
    'flonum', 'number', 'slider', 'dial', 'button', 'toggle', 'umenu',
    'textbox', 'message', 'bang', 'metro', 'loadbang', 'loadmess',
    'attrui', 'preset', 'pcontrol', 'key', 'keyup', 'mousestate',
    'ctlin', 'notein', 'pgmin', 'bendin', 'touchin', 'midiin'
}

GENERATOR_OBJECTS = {
    'cycle~', 'saw~', 'tri~', 'rect~', 'noise~', 'pink~', 'phasor~',
    'osc~', 'wavetable~', 'play~', 'sfplay~', 'groove~', 'buffer~',
    'sig~', 'line~', 'curve~', 'ramp~', 'adsr~', 'function',
    'rand', 'random', 'urn', 'drunk', 'lfo~', 'sinusoids~'
}

PROCESSOR_OBJECTS = {
    'gain~', 'filtergraph~', 'biquad~', 'lores~', 'hip~', 'lop~',
    'bandpass~', 'reson~', 'allpass~', 'comb~', 'delay~', 'tapin~', 'tapout~',
    'reverb~', 'freeverb~', 'gverb~', 'chorus~', 'flanger~', 'phaser~',
    'overdrive~', 'degrade~', 'bitcrush~', 'clip~', 'compress~', 'limiter~',
    'eq~', 'bpf~', 'cross~', 'gate~', 'thresh~', 'smooth~', 'slide~',
    '*~', '+~', '-~', '/~', '%~', 'pow~', 'abs~', 'sqrt~', 'log~', 'exp~',
    'sin~', 'cos~', 'tan~', 'tanh~', 'atan2~', 'cartopol~', 'poltocar~',
    'selector~', 'gate', 'switch', 'route', 'split', 'pack', 'unpack',
    'scale', 'expr', 'if', 'counter', 'accum', 'bucket', 'bag'
}

OUTPUT_OBJECTS = {
    'dac~', 'ezdac~', 'adc~', 'ezadc~', 'out~', 'send~', 'receive~',
    'throw~', 'catch~', 'print', 'post', 'error', 'meter~', 'scope~',
    'spectroscope~', 'spectrogram~', 'levelmeter~', 'vu~', 'peak~',
    'snapshot~', 'capture~', 'record~', 'sfrecord~', 'writesf~',
    'midiout', 'noteout', 'ctlout', 'pgmout', 'bendout', 'touchout'
}
    