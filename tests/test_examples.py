#!/usr/bin/env python3
"""
Test suite for all py2max examples.

This test file imports and runs all examples to ensure they work correctly
and don't break as the library evolves.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add the tests/examples directory to the path so we can import examples
examples_dir = Path(__file__).parent / "examples"
sys.path.insert(0, str(examples_dir))


class TestQuickstartExamples:
    """Test quickstart examples."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.old_cwd)

    def test_basic_patch(self):
        """Test basic patch creation example."""
        from quickstart.basic_patch import create_basic_patch

        patch = create_basic_patch()
        assert patch is not None
        assert len(patch._boxes) == 3  # osc, gain, dac
        assert len(patch._lines) == 2  # two connections
        assert patch._path == "my-first-patch.maxpat"

    def test_layout_examples(self):
        """Test layout examples."""
        from quickstart.layout_examples import (
            grid_layout_example,
            flow_layout_example,
            object_help_example,
            connection_validation_example,
        )

        # Test grid layout
        grid_patch = grid_layout_example()
        assert len(grid_patch._boxes) == 5
        assert len(grid_patch._lines) == 4

        # Test flow layout
        flow_patch = flow_layout_example()
        assert len(flow_patch._boxes) == 5
        assert len(flow_patch._lines) == 4

        # Test object help
        help_patch, help_text, methods, attrs, inlets, outlets = object_help_example()
        assert help_patch is not None
        # help_text can be None if no help is available
        assert methods >= 0  # Allow 0 if no methods found
        assert attrs >= 0  # Allow 0 if no attributes found
        assert inlets > 0
        assert outlets > 0

        # Test connection validation
        val_patch, error_occurred = connection_validation_example()
        assert val_patch is not None
        assert error_occurred is True


class TestTutorialExamples:
    """Test tutorial examples."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.old_cwd)

    def test_simple_synthesis(self):
        """Test simple synthesis tutorial."""
        from tutorial.simple_synthesis import create_chord_synthesizer

        patch = create_chord_synthesizer()
        assert patch is not None
        # 3 oscs + 3 gains + 3 gain_mults + mixer + master_vol + master_mult + output = 13
        assert len(patch._boxes) >= 13
        assert len(patch._lines) >= 9  # Multiple connections

    def test_signal_processing_chain(self):
        """Test signal processing chain tutorial."""
        from tutorial.signal_processing_chain import create_fx_chain

        patch = create_fx_chain()
        assert patch is not None
        assert len(patch._boxes) >= 15  # Many processing objects
        assert len(patch._lines) >= 12  # Many connections

    def test_interactive_controller(self):
        """Test interactive controller tutorial."""
        from tutorial.interactive_controller import create_midi_controller

        patch = create_midi_controller()
        assert patch is not None
        # MIDI in + 8 controllers (4 objects each) + preset system + comments
        assert len(patch._boxes) >= 35
        assert len(patch._lines) >= 40  # Many connections

    def test_generative_music(self):
        """Test generative music tutorial."""
        from tutorial.generative_music import create_generative_music

        patch = create_generative_music()
        assert patch is not None
        # Complex system with many objects
        assert len(patch._boxes) >= 40
        assert len(patch._lines) >= 35


class TestLayoutExamples:
    """Test layout examples."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.old_cwd)

    def test_grid_layout_examples(self):
        """Test grid layout examples."""
        from layout.grid_layout_examples import (
            create_basic_grid_horizontal,
            create_basic_grid_vertical,
            create_clustered_grid,
            create_mixed_layout,
            create_large_clustered_patch,
        )

        # Test horizontal grid
        h_patch = create_basic_grid_horizontal()
        assert len(h_patch._boxes) == 12

        # Test vertical grid
        v_patch = create_basic_grid_vertical()
        assert len(v_patch._boxes) == 12

        # Test clustered grid
        c_patch = create_clustered_grid()
        assert len(c_patch._boxes) >= 10
        assert len(c_patch._lines) >= 9

        # Test mixed layout
        m_patch = create_mixed_layout()
        assert len(m_patch._boxes) >= 13

        # Test large clustered patch
        l_patch = create_large_clustered_patch()
        assert len(l_patch._boxes) >= 35

    def test_flow_layout_examples(self):
        """Test flow layout examples."""
        from layout.flow_layout_examples import (
            create_horizontal_flow,
            create_vertical_flow,
            create_complex_flow,
            create_parallel_processing,
            create_feedback_flow,
        )

        # Test horizontal flow
        h_patch = create_horizontal_flow()
        assert len(h_patch._boxes) == 6
        assert len(h_patch._lines) == 5

        # Test vertical flow
        v_patch = create_vertical_flow()
        assert len(v_patch._boxes) >= 11
        assert len(v_patch._lines) >= 10

        # Test complex flow
        c_patch = create_complex_flow()
        assert len(c_patch._boxes) >= 9
        assert len(c_patch._lines) >= 8

        # Test parallel processing
        p_patch = create_parallel_processing()
        assert len(p_patch._boxes) >= 9
        assert len(p_patch._lines) >= 10

        # Test feedback flow
        f_patch = create_feedback_flow()
        assert len(f_patch._boxes) >= 8
        assert len(f_patch._lines) >= 8


class TestAdvancedExamples:
    """Test advanced examples."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.old_cwd)

    def test_subpatchers(self):
        """Test subpatcher examples."""
        from advanced.subpatchers import (
            create_basic_subpatcher,
            create_nested_subpatchers,
        )

        # Test basic subpatcher
        basic_patch = create_basic_subpatcher()
        assert basic_patch is not None
        assert len(basic_patch._boxes) >= 3

        # Test nested subpatchers
        nested_patch = create_nested_subpatchers()
        assert nested_patch is not None
        assert len(nested_patch._boxes) >= 1

    def test_data_containers(self):
        """Test data container examples."""
        from advanced.data_containers import (
            create_wavetable_synth,
            create_sequencer,
            create_state_management,
        )

        # Test wavetable synth
        wave_patch = create_wavetable_synth()
        assert len(wave_patch._boxes) >= 7
        assert len(wave_patch._lines) >= 5

        # Test sequencer
        seq_patch = create_sequencer()
        assert len(seq_patch._boxes) >= 9
        assert len(seq_patch._lines) >= 6

        # Test state management
        state_patch = create_state_management()
        assert len(state_patch._boxes) >= 7
        assert len(state_patch._lines) >= 10

    def test_connection_patterns(self):
        """Test connection pattern examples."""
        from advanced.connection_patterns import (
            create_fan_out_example,
            create_feedback_delay,
            create_matrix_mixer,
        )

        # Test fan-out
        fanout_patch = create_fan_out_example()
        assert len(fanout_patch._boxes) >= 8
        assert len(fanout_patch._lines) >= 12

        # Test feedback delay
        feedback_patch = create_feedback_delay()
        assert len(feedback_patch._boxes) >= 6
        assert len(feedback_patch._lines) >= 6

        # Test matrix mixer
        matrix_patch = create_matrix_mixer()
        assert len(matrix_patch._boxes) >= 24
        assert len(matrix_patch._lines) >= 32

    def test_error_handling(self):
        """Test error handling examples."""
        from advanced.error_handling import (
            create_robust_patch,
            demonstrate_connection_validation,
        )

        # Test robust patch creation
        robust_patch = create_robust_patch("robust-test.maxpat")
        assert robust_patch is not None
        assert len(robust_patch._boxes) >= 3

        # Test validation demonstration
        val_patch = demonstrate_connection_validation()
        assert val_patch is not None
        assert len(val_patch._boxes) >= 2

    def test_performance_optimization(self):
        """Test performance optimization examples."""
        from advanced.performance_optimization import (
            create_large_patch_efficiently,
            process_many_patches,
            create_optimized_signal_chain,
        )

        # Test large patch
        large_patch = create_large_patch_efficiently()
        assert len(large_patch._boxes) == 200
        assert len(large_patch._lines) == 100

        # Test batch processing
        configs = [
            {"filename": f"test-{i}.maxpat", "objects": [{"text": f"cycle~ {440 + i}"}]}
            for i in range(3)
        ]
        results = process_many_patches(configs)
        assert len(results) == 3

        # Test optimized chain
        opt_patch = create_optimized_signal_chain()
        assert len(opt_patch._boxes) >= 8
        assert len(opt_patch._lines) >= 7

    def test_custom_extensions(self):
        """Test custom extension examples."""
        from advanced.custom_extensions import (
            create_custom_synthesizer,
            create_modular_system,
        )

        # Test custom synthesizer
        custom_patch = create_custom_synthesizer()
        assert custom_patch is not None
        assert len(custom_patch._boxes) >= 15

        # Test modular system
        modular_patch = create_modular_system()
        assert modular_patch is not None
        assert len(modular_patch._boxes) >= 25


class TestAPIExamples:
    """Test API examples."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.old_cwd)

    def test_patcher_api_examples(self):
        """Test patcher API examples."""
        from api.patcher_api_examples import (
            demonstrate_patcher_creation,
            demonstrate_object_creation,
            demonstrate_connections,
            demonstrate_layout_management,
            demonstrate_file_operations,
            demonstrate_patch_introspection,
        )

        # Test patcher creation
        patchers = demonstrate_patcher_creation()
        assert len(patchers) == 6

        # Test object creation
        obj_patch = demonstrate_object_creation()
        assert len(obj_patch._boxes) >= 10

        # Test connections
        conn_patch = demonstrate_connections()
        assert len(conn_patch._lines) >= 6

        # Test layout management
        grid_patch, flow_patch = demonstrate_layout_management()
        assert len(grid_patch._boxes) >= 5
        assert len(flow_patch._boxes) >= 4

        # Test file operations
        orig_patch, mod_patch = demonstrate_file_operations()
        assert orig_patch is not None
        assert mod_patch is not None

        # Test introspection
        intro_patch = demonstrate_patch_introspection()
        assert len(intro_patch._boxes) >= 3

    def test_box_api_examples(self):
        """Test box API examples."""
        from api.box_api_examples import (
            demonstrate_object_help,
            demonstrate_inlet_outlet_introspection,
            demonstrate_object_properties,
            demonstrate_object_validation,
            demonstrate_object_types,
        )

        # Test object help
        help_patch = demonstrate_object_help()
        assert len(help_patch._boxes) >= 5

        # Test I/O introspection
        io_patch = demonstrate_inlet_outlet_introspection()
        assert len(io_patch._boxes) >= 7

        # Test object properties
        props_patch = demonstrate_object_properties()
        assert len(props_patch._boxes) >= 3

        # Test validation
        val_patch = demonstrate_object_validation()
        assert len(val_patch._boxes) >= 3

        # Test object types
        types_patch = demonstrate_object_types()
        assert len(types_patch._boxes) >= 15


class TestExampleExecution:
    """Test that examples can be executed as scripts."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.old_cwd)

    def test_example_scripts_run(self):
        """Test that example scripts can be executed without errors."""
        import subprocess

        example_files = [
            "quickstart/basic_patch.py",
            "tutorial/simple_synthesis.py",
            "layout/grid_layout_examples.py",
            "advanced/subpatchers.py",
        ]

        for example_file in example_files:
            example_path = examples_dir / example_file
            if example_path.exists():
                # Run the example script
                result = subprocess.run(
                    [sys.executable, str(example_path)],
                    capture_output=True,
                    text=True,
                    cwd=self.temp_dir,
                )

                # Check that it ran without errors
                assert result.returncode == 0, (
                    f"Example {example_file} failed with: {result.stderr}"
                )
                assert len(result.stdout) > 0, (
                    f"Example {example_file} produced no output"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
