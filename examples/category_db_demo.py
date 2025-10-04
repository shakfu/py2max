#!/usr/bin/env python3
"""Demonstration of category-based database population

This example shows how to:
1. Populate databases with specific Max object categories
2. Query objects by category
3. Compare category sizes
"""

from pathlib import Path
from py2max import MaxRefDB
from py2max.maxref import (
    get_all_max_objects,
    get_all_jit_objects,
    get_all_msp_objects,
    get_all_m4l_objects,
    get_objects_by_category,
)

def main():
    print("=== Max Object Category Database Demo ===\n")

    # Example 1: Get object counts by category
    print("1. Object counts by category:")
    max_objects = get_all_max_objects()
    jit_objects = get_all_jit_objects()
    msp_objects = get_all_msp_objects()
    m4l_objects = get_all_m4l_objects()

    print(f"   Max objects (max-ref):  {len(max_objects)}")
    print(f"   Jitter objects (jit-ref): {len(jit_objects)}")
    print(f"   MSP objects (msp-ref):    {len(msp_objects)}")
    print(f"   M4L objects (m4l-ref):    {len(m4l_objects)}")
    print(f"   Total objects:            {len(max_objects) + len(jit_objects) + len(msp_objects) + len(m4l_objects)}\n")

    # Example 2: Show sample objects from each category
    print("2. Sample objects from each category:")
    print(f"   Max: {', '.join(max_objects[:5])}")
    print(f"   Jitter: {', '.join(jit_objects[:5])}")
    print(f"   MSP: {', '.join(msp_objects[:5])}")
    print(f"   M4L: {', '.join(m4l_objects[:5])}\n")

    # Example 3: Create category-specific databases
    print("3. Creating category-specific databases...")

    # Max objects only
    db_max = MaxRefDB()
    db_max.populate_all_max_objects()
    print(f"   Max database: {db_max.get_object_count()} objects")

    # MSP objects only
    db_msp = MaxRefDB()
    db_msp.populate_all_msp_objects()
    print(f"   MSP database: {db_msp.get_object_count()} objects")

    # Jitter objects only
    db_jit = MaxRefDB()
    db_jit.populate_all_jit_objects()
    print(f"   Jitter database: {db_jit.get_object_count()} objects")

    # M4L objects only
    db_m4l = MaxRefDB()
    db_m4l.populate_all_m4l_objects()
    print(f"   M4L database: {db_m4l.get_object_count()} objects\n")

    # Example 4: Create complete database with all objects
    print("4. Creating complete database with all categories...")
    db_all = MaxRefDB()
    db_all.populate_all_objects()
    print(f"   Complete database: {db_all.get_object_count()} objects\n")

    # Example 5: Query specific objects from category databases
    print("5. Querying specific objects from category databases:")

    # Query cycle~ from MSP database
    cycle = db_msp.get_object('cycle~')
    if cycle:
        print(f"   cycle~ (MSP): {cycle.get('digest', 'N/A')}")
        print(f"     - Inlets: {len(cycle.get('inlets', []))}")
        print(f"     - Outlets: {len(cycle.get('outlets', []))}")

    # Query metro from Max database
    metro = db_max.get_object('metro')
    if metro:
        print(f"   metro (Max): {metro.get('digest', 'N/A')}")
        print(f"     - Methods: {len(metro.get('methods', {}))}")

    print()

    # Example 6: Create persistent category databases
    print("6. Creating persistent category database files...")
    output_dir = Path("outputs/category_dbs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create file-based databases for each category
    categories = {
        'max': db_max,
        'msp': db_msp,
        'jit': db_jit,
        'm4l': db_m4l,
    }

    for category, db_instance in categories.items():
        db_path = output_dir / f"{category}_objects.db"
        # Create new file-based database
        file_db = MaxRefDB(db_path)

        # Use the appropriate populate method
        if category == 'max':
            file_db.populate_all_max_objects()
        elif category == 'msp':
            file_db.populate_all_msp_objects()
        elif category == 'jit':
            file_db.populate_all_jit_objects()
        elif category == 'm4l':
            file_db.populate_all_m4l_objects()

        print(f"   Created {db_path.name}: {file_db.get_object_count()} objects")

    print()

    # Example 7: Generic category query
    print("7. Using generic get_objects_by_category function:")
    for category in ['max', 'msp', 'jit', 'm4l']:
        objects = get_objects_by_category(category)
        print(f"   {category}: {len(objects)} objects (e.g., {', '.join(objects[:3])})")

    print("\nDemo complete!")
    print(f"\nCategory database files created in: {output_dir}")

if __name__ == "__main__":
    main()
