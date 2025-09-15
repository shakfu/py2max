#!/usr/bin/env python3
"""
Advanced Usage: Performance Optimization
=========================================

Examples demonstrating optimization for large patches and memory management.

This example is used in:
- docs/source/user_guide/advanced_usage.rst
"""

from py2max import Patcher


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
    p.save()

    return p


def process_many_patches(patch_configs):
    """Process multiple patches with memory management."""
    results = []

    for config in patch_configs:
        # Create patch
        p = Patcher(config['filename'])

        # Add objects based on config
        for obj_config in config['objects']:
            p.add_textbox(obj_config['text'])

        # Process and save
        p.optimize_layout()
        p.save()

        # Store results before cleanup
        results.append({
            'filename': config['filename'],
            'object_count': len(p._boxes)
        })

        # Explicit cleanup for large numbers of patches
        del p

    return results


def create_optimized_signal_chain():
    """Create an optimized signal processing chain."""
    # Use flow layout for optimal signal routing
    p = Patcher('optimized-chain.maxpat', layout="flow", flow_direction="horizontal")

    # Create signal chain efficiently
    signal_chain = []

    # Input
    input_obj = p.add_textbox('adc~')
    signal_chain.append(input_obj)

    # Processing chain
    processors = [
        'biquad~ 100 0.707 highpass',
        '*~ 2.0',
        'tanh~',
        'biquad~ 5000 0.707 lowpass',
        'delay~ 250',
        '*~ 0.7'
    ]

    for processor in processors:
        proc_obj = p.add_textbox(processor)
        signal_chain.append(proc_obj)

    # Output
    output_obj = p.add_textbox('dac~')
    signal_chain.append(output_obj)

    # Connect chain efficiently
    for i in range(len(signal_chain) - 1):
        p.add_line(signal_chain[i], signal_chain[i + 1])

    # Single optimization pass
    p.optimize_layout()
    p.save()

    return p


if __name__ == '__main__':
    # Create large patch efficiently
    large_patch = create_large_patch_efficiently()
    print(f"Created large patch with {len(large_patch._boxes)} objects")

    # Process multiple patches
    patch_configs = [
        {
            'filename': f'batch-patch-{i}.maxpat',
            'objects': [
                {'text': f'cycle~ {440 + i * 110}'},
                {'text': 'gain~'},
                {'text': 'ezdac~'}
            ]
        }
        for i in range(5)
    ]

    results = process_many_patches(patch_configs)
    print(f"Processed {len(results)} patches in batch")

    # Create optimized signal chain
    optimized_patch = create_optimized_signal_chain()
    print(f"Created optimized signal chain with {len(optimized_patch._boxes)} objects")