"""Tests for SQLite database functionality"""

import json
import tempfile
from pathlib import Path

import pytest

from py2max.db import MaxRefDB
from py2max.maxref import get_object_info


class TestMaxRefDB:
    """Test MaxRefDB class"""

    def test_init_in_memory(self):
        """Test initialization with in-memory database"""
        db = MaxRefDB(":memory:", auto_populate=False)
        assert db.db_path == ":memory:"
        # Test both new property and deprecated method
        assert db.count == 0
        assert db.get_object_count() == 0
        assert len(db) == 0

    def test_init_with_file(self):
        """Test initialization with file-based database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = MaxRefDB(db_path)
            assert db.db_path == db_path
            assert db_path.exists()

    def test_schema_creation(self):
        """Test that all tables are created"""
        db = MaxRefDB(":memory:", auto_populate=False)
        with db._get_cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row['name'] for row in cursor.fetchall()]

            expected_tables = [
                'attribute_enums',
                'attributes',
                'examples',
                'inlets',
                'metadata',
                'method_args',
                'methods',
                'misc',
                'objargs',
                'objects',
                'outlets',
                'palette',
                'parameter',
                'seealso',
            ]

            # Filter out sqlite_sequence which is auto-created by SQLite
            tables = [t for t in tables if t != 'sqlite_sequence']
            assert sorted(tables) == sorted(expected_tables)

    def test_insert_and_get_simple_object(self):
        """Test inserting and retrieving a simple object"""
        db = MaxRefDB(":memory:", auto_populate=False)

        # Create simple test data
        test_data = {
            'name': 'test_obj',
            'digest': 'Test object digest',
            'description': 'Test object description',
            'category': 'test',
            'metadata': {'tag': 'test_tag'},
            'inlets': [{'id': '0', 'type': 'signal', 'digest': 'Input signal'}],
            'outlets': [{'id': '0', 'type': 'signal', 'digest': 'Output signal'}],
            'objargs': [],
            'methods': {},
            'attributes': {},
            'examples': [],
            'seealso': [],
            'misc': {},
            'palette': {},
            'parameter': {},
        }

        obj_id = db.insert_object('test_obj', test_data)
        assert obj_id > 0

        # Retrieve and verify
        retrieved = db.get_object('test_obj')
        assert retrieved is not None
        assert retrieved['name'] == 'test_obj'
        assert retrieved['digest'] == 'Test object digest'
        assert retrieved['description'] == 'Test object description'
        assert retrieved['category'] == 'test'
        assert retrieved['metadata']['tag'] == 'test_tag'
        assert len(retrieved['inlets']) == 1
        assert len(retrieved['outlets']) == 1

    def test_insert_complex_object(self):
        """Test inserting an object with complex nested data"""
        db = MaxRefDB(":memory:", auto_populate=False)

        test_data = {
            'name': 'complex_obj',
            'digest': 'Complex object',
            'description': 'A complex test object',
            'metadata': {
                'author': 'Test Author',
                'tag': ['audio', 'signal', 'filter']  # Multiple tags
            },
            'inlets': [
                {'id': '0', 'type': 'signal', 'digest': 'Input'},
                {'id': '1', 'type': 'float', 'digest': 'Frequency'}
            ],
            'outlets': [
                {'id': '0', 'type': 'signal', 'digest': 'Output'}
            ],
            'objargs': [
                {'name': 'frequency', 'optional': '0', 'type': 'float', 'digest': 'Initial frequency'}
            ],
            'methods': {
                'bang': {
                    'digest': 'Output current value',
                    'description': 'Outputs the current value',
                    'args': []
                },
                'int': {
                    'digest': 'Set frequency',
                    'description': 'Sets the frequency to the input value',
                    'args': [
                        {'name': 'value', 'type': 'int', 'optional': '0'}
                    ]
                }
            },
            'attributes': {
                'frequency': {
                    'name': 'frequency',
                    'type': 'float',
                    'get': '1',
                    'set': '1',
                    'digest': 'Frequency in Hz',
                    'description': 'Sets the frequency of the oscillator',
                    'enumlist': []
                },
                'mode': {
                    'name': 'mode',
                    'type': 'symbol',
                    'get': '1',
                    'set': '1',
                    'digest': 'Operation mode',
                    'enumlist': [
                        {'name': 'lowpass', 'digest': 'Low-pass filter'},
                        {'name': 'highpass', 'digest': 'High-pass filter'}
                    ]
                }
            },
            'examples': [
                {'name': 'basic', 'caption': 'Basic usage'}
            ],
            'seealso': ['related_obj1', 'related_obj2'],
            'misc': {
                'Output': {
                    'signal': 'Filtered signal'
                }
            },
            'palette': {
                'category': 'MSP Filters',
                'palette_index': '5'
            },
            'parameter': {
                'enable': '1'
            }
        }

        obj_id = db.insert_object('complex_obj', test_data)
        assert obj_id > 0

        # Retrieve and verify
        retrieved = db.get_object('complex_obj')
        assert retrieved is not None

        # Verify metadata with multiple values
        assert retrieved['metadata']['author'] == 'Test Author'
        assert isinstance(retrieved['metadata']['tag'], list)
        assert 'audio' in retrieved['metadata']['tag']
        assert 'signal' in retrieved['metadata']['tag']
        assert 'filter' in retrieved['metadata']['tag']

        # Verify inlets and outlets
        assert len(retrieved['inlets']) == 2
        assert len(retrieved['outlets']) == 1

        # Verify methods
        assert 'bang' in retrieved['methods']
        assert 'int' in retrieved['methods']
        assert len(retrieved['methods']['int']['args']) == 1

        # Verify attributes with enums
        assert 'frequency' in retrieved['attributes']
        assert 'mode' in retrieved['attributes']
        assert len(retrieved['attributes']['mode']['enumlist']) == 2

        # Verify examples and seealso
        assert len(retrieved['examples']) == 1
        assert len(retrieved['seealso']) == 2
        assert 'related_obj1' in retrieved['seealso']

        # Verify misc
        assert 'Output' in retrieved['misc']

        # Verify palette
        assert retrieved['palette']['category'] == 'MSP Filters'

    def test_populate_from_maxref(self):
        """Test populating database from .maxref.xml files"""
        db = MaxRefDB(":memory:", auto_populate=False)

        # Test new populate() method
        db.populate(['cycle~', 'gain~', 'dac~'])

        assert db.count == 3
        assert len(db) == 3

        # Test __contains__
        assert 'cycle~' in db
        assert 'nonexistent' not in db

        # Test __getitem__
        cycle = db['cycle~']
        assert cycle is not None
        assert 'cycle' in cycle['name'] or cycle['name'] == 'cycle~'

        # Test that KeyError is raised for nonexistent object
        try:
            _ = db['nonexistent']
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert 'nonexistent' in str(e)

        # Compare with direct maxref access
        cycle_ref = get_object_info('cycle~')
        if cycle_ref:
            assert cycle['digest'] == cycle_ref.get('digest')

        # Test deprecated method still works
        db2 = MaxRefDB(":memory:", auto_populate=False)
        db2.populate_from_maxref(['cycle~'])
        assert db2.get_object_count() == 1

    def test_search_objects(self):
        """Test searching for objects"""
        db = MaxRefDB(":memory:", auto_populate=False)

        # Insert test objects
        test_objects = [
            {'name': 'audio_filter', 'digest': 'Filters audio signals', 'description': 'A filter', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
            {'name': 'signal_gen', 'digest': 'Generates signals', 'description': 'Signal generator', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
            {'name': 'dsp_effect', 'digest': 'DSP effect', 'description': 'Applies audio effect', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
        ]

        for obj in test_objects:
            db.insert_object(obj['name'], obj)

        # Test new search() method
        results = db.search('filter')
        assert 'audio_filter' in results

        # Search by digest
        results = db.search('signals')
        assert 'audio_filter' in results
        assert 'signal_gen' in results

        # Search by description
        results = db.search('effect')
        assert 'dsp_effect' in results

        # Test deprecated method still works
        results = db.search_objects('filter')
        assert 'audio_filter' in results

    def test_get_objects_by_category(self):
        """Test getting objects by category"""
        db = MaxRefDB(":memory:", auto_populate=False)

        test_objects = [
            {'name': 'obj1', 'category': 'audio', 'digest': '', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
            {'name': 'obj2', 'category': 'audio', 'digest': '', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
            {'name': 'obj3', 'category': 'video', 'digest': '', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
        ]

        for obj in test_objects:
            db.insert_object(obj['name'], obj)

        # Test new by_category() method
        audio_objects = db.by_category('audio')
        assert len(audio_objects) == 2
        assert 'obj1' in audio_objects
        assert 'obj2' in audio_objects

        video_objects = db.by_category('video')
        assert len(video_objects) == 1
        assert 'obj3' in video_objects

        # Test deprecated method still works
        audio_objects = db.get_objects_by_category('audio')
        assert len(audio_objects) == 2

    def test_get_all_categories(self):
        """Test getting all unique categories"""
        db = MaxRefDB(":memory:", auto_populate=False)

        test_objects = [
            {'name': 'obj1', 'category': 'audio', 'digest': '', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
            {'name': 'obj2', 'category': 'video', 'digest': '', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
            {'name': 'obj3', 'category': 'audio', 'digest': '', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
            {'name': 'obj4', 'category': 'control', 'digest': '', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
        ]

        for obj in test_objects:
            db.insert_object(obj['name'], obj)

        # Test new categories property
        categories = db.categories
        assert len(categories) == 3
        assert 'audio' in categories
        assert 'video' in categories
        assert 'control' in categories

        # Test deprecated method still works
        categories = db.get_all_categories()
        assert len(categories) == 3

    def test_export_import_json(self):
        """Test exporting and importing database as JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and populate database
            db1 = MaxRefDB(":memory:", auto_populate=False)
            test_data = {
                'name': 'test_export',
                'digest': 'Test export',
                'description': 'Test object for export',
                'metadata': {'tag': 'test'},
                'inlets': [{'id': '0', 'type': 'signal'}],
                'outlets': [{'id': '0', 'type': 'signal'}],
                'objargs': [],
                'methods': {'bang': {'digest': 'Bang method'}},
                'attributes': {},
                'examples': [],
                'seealso': ['other_obj'],
                'misc': {},
                'palette': {},
                'parameter': {},
            }
            db1.insert_object('test_export', test_data)

            # Test new export() method
            json_path = Path(tmpdir) / "export.json"
            db1.export(json_path)
            assert json_path.exists()

            # Test new load() method
            db2 = MaxRefDB(":memory:", auto_populate=False)
            db2.load(json_path)

            # Verify imported data
            imported = db2['test_export']
            assert imported is not None
            assert imported['digest'] == 'Test export'
            assert len(imported['inlets']) == 1
            assert 'bang' in imported['methods']

            # Test deprecated methods still work
            json_path2 = Path(tmpdir) / "export2.json"
            db1.export_to_json(json_path2)
            db3 = MaxRefDB(":memory:", auto_populate=False)
            db3.import_from_json(json_path2)
            assert db3.get_object('test_export') is not None

    def test_create_database_function(self):
        """Test the create_database convenience function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create without populating
            db1 = MaxRefDB.create_database(db_path, populate=False)
            assert db1.get_object_count() == 0

            # Create with populating (limit to a few objects for speed)
            db2 = MaxRefDB(":memory:", auto_populate=False)
            db2.populate_from_maxref(['cycle~', 'gain~'])
            assert db2.get_object_count() == 2

    def test_replace_object(self):
        """Test that inserting an object twice replaces the first"""
        db = MaxRefDB(":memory:", auto_populate=False)

        # Insert original
        data1 = {
            'name': 'test_replace',
            'digest': 'Original digest',
            'description': 'Original description',
            'metadata': {},
            'inlets': [{'id': '0', 'type': 'signal'}],
            'outlets': [],
            'objargs': [],
            'methods': {},
            'attributes': {},
            'examples': [],
            'seealso': [],
            'misc': {},
            'palette': {},
            'parameter': {},
        }
        db.insert_object('test_replace', data1)

        # Insert replacement
        data2 = {
            'name': 'test_replace',
            'digest': 'Updated digest',
            'description': 'Updated description',
            'metadata': {},
            'inlets': [{'id': '0', 'type': 'int'}, {'id': '1', 'type': 'float'}],
            'outlets': [],
            'objargs': [],
            'methods': {},
            'attributes': {},
            'examples': [],
            'seealso': [],
            'misc': {},
            'palette': {},
            'parameter': {},
        }
        db.insert_object('test_replace', data2)

        # Verify only one object exists with updated data
        assert db.get_object_count() == 1
        obj = db.get_object('test_replace')
        assert obj['digest'] == 'Updated digest'
        assert obj['description'] == 'Updated description'
        assert len(obj['inlets']) == 2

    def test_get_nonexistent_object(self):
        """Test getting an object that doesn't exist"""
        db = MaxRefDB(":memory:", auto_populate=False)
        result = db.get_object('nonexistent_object')
        assert result is None

    def test_empty_search(self):
        """Test searching with no matches"""
        db = MaxRefDB(":memory:", auto_populate=False)
        results = db.search_objects('nonexistent_query')
        assert len(results) == 0

    def test_root_attributes_preservation(self):
        """Test that root-level attributes are preserved"""
        db = MaxRefDB(":memory:", auto_populate=False)

        test_data = {
            'name': 'test_root',
            'digest': 'Test',
            'description': 'Test',
            'custom_field': 'custom_value',
            'nested_field': {'key': 'value'},
            'metadata': {},
            'inlets': [],
            'outlets': [],
            'objargs': [],
            'methods': {},
            'attributes': {},
            'examples': [],
            'seealso': [],
            'misc': {},
            'palette': {},
            'parameter': {},
        }

        db.insert_object('test_root', test_data)
        retrieved = db.get_object('test_root')

        assert 'custom_field' in retrieved
        assert retrieved['custom_field'] == 'custom_value'
        assert 'nested_field' in retrieved
        assert retrieved['nested_field']['key'] == 'value'

    def test_populate_by_category(self):
        """Test populating database by Max object category"""
        # Test Max objects with new populate() API
        db_max = MaxRefDB(":memory:", auto_populate=False)
        db_max.populate(category='max')
        assert db_max.count > 0
        max_count = db_max.count

        # Test MSP objects with new populate() API
        db_msp = MaxRefDB(":memory:", auto_populate=False)
        db_msp.populate(category='msp')
        assert db_msp.count > 0
        msp_count = db_msp.count

        # Test Jitter objects with new populate() API
        db_jit = MaxRefDB(":memory:", auto_populate=False)
        db_jit.populate(category='jit')
        assert db_jit.count > 0
        jit_count = db_jit.count

        # Test M4L objects with new populate() API
        db_m4l = MaxRefDB(":memory:", auto_populate=False)
        db_m4l.populate(category='m4l')
        assert db_m4l.count > 0
        m4l_count = db_m4l.count

        # Test all objects with new populate() API
        db_all = MaxRefDB(":memory:", auto_populate=False)
        db_all.populate()  # No category = all
        all_count = db_all.count

        # All objects should be sum of all categories
        assert all_count == max_count + msp_count + jit_count + m4l_count

        # Verify some known objects are in the right categories
        # cycle~ should be in MSP
        if 'cycle~' in db_msp:
            assert db_msp['cycle~'] is not None

        # Test deprecated methods still work
        db_test = MaxRefDB(":memory:", auto_populate=False)
        db_test.populate_all_msp_objects()
        assert db_test.get_object_count() > 0

    def test_category_helpers(self):
        """Test category helper functions from maxref"""
        from py2max.maxref import (
            get_all_max_objects,
            get_all_jit_objects,
            get_all_msp_objects,
            get_all_m4l_objects,
            get_objects_by_category,
        )

        # Get objects by category
        max_objects = get_all_max_objects()
        jit_objects = get_all_jit_objects()
        msp_objects = get_all_msp_objects()
        m4l_objects = get_all_m4l_objects()

        # All should return lists
        assert isinstance(max_objects, list)
        assert isinstance(jit_objects, list)
        assert isinstance(msp_objects, list)
        assert isinstance(m4l_objects, list)

        # All should have some objects
        assert len(max_objects) > 0
        assert len(jit_objects) > 0
        assert len(msp_objects) > 0
        assert len(m4l_objects) > 0

        # Test generic get_objects_by_category
        assert get_objects_by_category('max') == max_objects
        assert get_objects_by_category('jit') == jit_objects
        assert get_objects_by_category('msp') == msp_objects
        assert get_objects_by_category('m4l') == m4l_objects

        # Known objects should be in correct categories
        # cycle~ is an MSP object
        assert 'cycle~' in msp_objects

        # No overlaps between categories
        assert not set(max_objects) & set(jit_objects)
        assert not set(max_objects) & set(msp_objects)
        assert not set(jit_objects) & set(msp_objects)

    def test_new_convenience_methods(self):
        """Test new convenience methods and properties"""
        db = MaxRefDB(":memory:", auto_populate=False)

        # Add some test objects
        test_objects = [
            {'name': 'obj1', 'category': 'audio', 'digest': 'Audio obj', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
            {'name': 'obj2', 'category': 'audio', 'digest': 'Audio obj 2', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
            {'name': 'obj3', 'category': 'video', 'digest': 'Video obj', 'description': '', 'metadata': {}, 'inlets': [], 'outlets': [], 'objargs': [], 'methods': {}, 'attributes': {}, 'examples': [], 'seealso': [], 'misc': {}, 'palette': {}, 'parameter': {}},
        ]

        for obj in test_objects:
            db.insert_object(obj['name'], obj)

        # Test .objects property
        all_objects = db.objects
        assert isinstance(all_objects, list)
        assert len(all_objects) == 3
        assert 'obj1' in all_objects
        assert 'obj2' in all_objects
        assert 'obj3' in all_objects

        # Test .summary() method
        summary = db.summary()
        assert summary['total_objects'] == 3
        assert 'audio' in summary['categories']
        assert 'video' in summary['categories']
        assert summary['categories']['audio'] == 2
        assert summary['categories']['video'] == 1

        # Test __repr__
        repr_str = repr(db)
        assert 'MaxRefDB' in repr_str
        assert 'in-memory' in repr_str
        assert '3 objects' in repr_str

        # Test with file-based database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db_file = MaxRefDB(db_path, auto_populate=False)
            repr_str = repr(db_file)
            assert 'test.db' in repr_str
            assert '0 objects' in repr_str

    def test_cache_functions(self):
        """Test cache directory static methods"""
        import sys

        cache_dir = MaxRefDB.get_cache_dir()
        assert cache_dir.exists()
        assert cache_dir.is_dir()

        # Check platform-specific paths
        if sys.platform == 'darwin':
            assert 'Library/Caches/py2max' in str(cache_dir)
        elif sys.platform == 'win32':
            assert 'AppData' in str(cache_dir) and 'py2max' in str(cache_dir)
        else:  # Linux
            assert '.cache/py2max' in str(cache_dir)

        db_path = MaxRefDB.get_default_db_path()
        assert db_path == cache_dir / 'maxref.db'

    def test_auto_populate(self, monkeypatch):
        """Test auto-population with cache"""
        import tempfile
        from py2max import db as db_module

        # Use temp directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            test_cache = Path(tmpdir) / 'maxref.db'

            # Patch static method on MaxRefDB class (static methods don't receive self)
            @staticmethod
            def mock_get_default_db_path():
                return test_cache

            monkeypatch.setattr(MaxRefDB, 'get_default_db_path', mock_get_default_db_path)

            # Also patch maxref functions
            def mock_get_available_objects():
                return ['cycle~', 'gain~']

            def mock_get_object_info(name):
                return {
                    'name': name,
                    'digest': f'Test {name}',
                    'description': f'Test object {name}',
                    'category': 'MSP',
                    'metadata': {},
                    'inlets': [],
                    'outlets': [],
                    'objargs': [],
                    'methods': {},
                    'attributes': {},
                    'examples': [],
                    'seealso': [],
                    'misc': {},
                    'palette': {},
                    'parameter': {},
                }

            monkeypatch.setattr(db_module, 'get_available_objects', mock_get_available_objects)
            monkeypatch.setattr(db_module, 'get_object_info', mock_get_object_info)

            # First call should auto-populate
            db = MaxRefDB(auto_populate=True)
            assert db.count == 2
            assert test_cache.exists()

            # Second call should use existing cache
            db2 = MaxRefDB(auto_populate=True)
            assert db2.count == 2
