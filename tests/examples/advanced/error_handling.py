#!/usr/bin/env python3
"""
Advanced Usage: Error Handling and Robustness
==============================================

Examples demonstrating error handling, validation, and robust patch creation.

This example is used in:
- docs/source/user_guide/advanced_usage.rst
"""

from py2max import Patcher, InvalidConnectionError
import logging


def create_robust_patch(filename):
    """Create a patch with comprehensive error handling."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

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
            # Find objects by ID
            src_obj = None
            dst_obj = None

            for obj in patcher._boxes:
                if obj.id == line.src:
                    src_obj = obj
                if obj.id == line.dst:
                    dst_obj = obj

            if src_obj and dst_obj:
                src_outlets = src_obj.get_outlet_count()
                dst_inlets = dst_obj.get_inlet_count()

                if hasattr(line, 'outlet') and line.outlet >= src_outlets:
                    errors.append(f"Invalid outlet {line.outlet} on {src_obj.maxclass}")

                if hasattr(line, 'inlet') and line.inlet >= dst_inlets:
                    errors.append(f"Invalid inlet {line.inlet} on {dst_obj.maxclass}")

        except Exception as e:
            errors.append(f"Error validating connection: {e}")

    return errors, warnings


def demonstrate_connection_validation():
    """Demonstrate connection validation features."""
    from py2max import InvalidConnectionError

    p = Patcher('validation-demo.maxpat', validate_connections=True)

    try:
        osc = p.add_textbox('cycle~ 440')
        gain = p.add_textbox('gain~')

        # This connection is valid
        p.add_line(osc, gain)
        print("Valid connection succeeded")

        # This would raise an error
        try:
            p.add_line(osc, gain, outlet=10)  # cycle~ doesn't have outlet 10
        except InvalidConnectionError as e:
            print(f"Invalid connection caught: {e}")

    except InvalidConnectionError as e:
        print(f"Connection error: {e}")
        # Handle error gracefully

    # Check object capabilities
    print(f"Oscillator outlets: {osc.get_outlet_count()}")
    print(f"Gain inlets: {gain.get_inlet_count()}")

    # Validate the patch structure
    errors, warnings = validate_patch_structure(p)
    if errors:
        print(f"Patch errors: {errors}")
    if warnings:
        print(f"Patch warnings: {warnings}")

    p.save()
    return p


if __name__ == '__main__':
    # Create robust patch
    robust_patch = create_robust_patch('robust-patch.maxpat')
    if robust_patch:
        print(f"Created robust patch with {len(robust_patch._boxes)} objects")

    # Demonstrate validation
    validation_patch = demonstrate_connection_validation()
    print(f"Created validation demo with {len(validation_patch._boxes)} objects")