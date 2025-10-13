#!/usr/bin/env python3
"""Demonstration of SQLite database functionality for Max object reference data

This example shows how to:
1. Create a SQLite database from .maxref.xml files
2. Query and search objects
3. Export/import database to JSON
"""

from pathlib import Path
from py2max import MaxRefDB, create_database


def main():
    print("=== MaxRefDB Demo ===\n")

    # Example 1: Create in-memory database and populate with a few objects
    print("1. Creating in-memory database...")
    db = MaxRefDB()
    db.populate_from_maxref(["cycle~", "gain~", "dac~", "umenu", "button"])
    print(f"   Populated with {db.get_object_count()} objects\n")

    # Example 2: Query specific object
    print("2. Querying 'cycle~' object...")
    cycle = db.get_object("cycle~")
    if cycle:
        print(f"   Name: {cycle['name']}")
        print(f"   Digest: {cycle.get('digest', 'N/A')}")
        print(f"   Inlets: {len(cycle.get('inlets', []))}")
        print(f"   Outlets: {len(cycle.get('outlets', []))}")
        print(f"   Methods: {len(cycle.get('methods', {}))}")
        print(f"   Attributes: {len(cycle.get('attributes', {}))}\n")

    # Example 3: Search for objects
    print("3. Searching for objects containing 'signal'...")
    results = db.search_objects("signal")
    print(f"   Found {len(results)} objects: {', '.join(results[:5])}\n")

    # Example 4: Get all categories
    print("4. Getting all unique categories...")
    categories = db.get_all_categories()
    print(f"   Found {len(categories)} categories")
    if categories:
        print(f"   Examples: {', '.join(categories[:3])}\n")

    # Example 5: Create file-based database
    print("5. Creating file-based database...")
    db_path = Path("outputs/maxref.db")
    db_path.parent.mkdir(exist_ok=True)

    file_db = create_database(db_path, populate=False)
    # Populate with specific objects for faster demo
    file_db.populate_from_maxref(
        [
            "cycle~",
            "saw~",
            "rect~",
            "tri~",
            "noise~",  # Generators
            "gain~",
            "lores~",
            "reson~",
            "delay~",  # Processors
            "dac~",
            "ezdac~",
            "meter~",  # Outputs
            "umenu",
            "button",
            "toggle",
            "slider",  # UI
        ]
    )
    print(f"   Created {db_path}")
    print(f"   Populated with {file_db.get_object_count()} objects\n")

    # Example 6: Export to JSON
    print("6. Exporting database to JSON...")
    json_path = Path("outputs/maxref_export.json")
    file_db.export_to_json(json_path)
    print(f"   Exported to {json_path}")
    print(f"   File size: {json_path.stat().st_size / 1024:.2f} KB\n")

    # Example 7: Query by category
    print("7. Querying objects by category...")
    msp_objects = file_db.get_objects_by_category("MSP")
    if msp_objects:
        print(f"   Found {len(msp_objects)} MSP objects")
        print(f"   Examples: {', '.join(msp_objects[:5])}\n")

    # Example 8: Import from JSON to new database
    print("8. Importing from JSON to new database...")
    new_db = MaxRefDB()
    new_db.import_from_json(json_path)
    print(f"   Imported {new_db.get_object_count()} objects\n")

    # Example 9: Complex query - find all objects with 'filter' in description
    print("9. Finding objects with 'filter' in description...")
    filter_objects = file_db.search_objects("filter", fields=["description"])
    print(f"   Found {len(filter_objects)} objects: {', '.join(filter_objects[:5])}\n")

    print("Demo complete!")
    print("\nOutput files created:")
    print(f"  - {db_path}")
    print(f"  - {json_path}")


if __name__ == "__main__":
    main()
