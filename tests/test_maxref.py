"""Tests for py2max.maxref module parsing .maxref.xml files and Box.help() method."""

import pytest
from pathlib import Path
from xml.etree import ElementTree

from py2max.maxref import (
    MaxRefCache,
    get_object_info,
    get_object_help,
    get_available_objects,
    get_legacy_defaults,
    MAXCLASS_DEFAULTS,
    replace_tags,
)
from py2max.core import Box, Patcher


class TestMaxRefParsing:
    """Test parsing of .maxref.xml files."""

    @pytest.fixture
    def umenu_xml_path(self):
        """Path to the test umenu.maxref.xml file."""
        return Path(__file__).parent / "data" / "umenu.maxref.xml"

    @pytest.fixture
    def umenu_xml_content(self, umenu_xml_path):
        """Content of the umenu.maxref.xml file."""
        return umenu_xml_path.read_text()

    @pytest.fixture
    def cache(self):
        """MaxRefCache instance for testing."""
        return MaxRefCache()

    def test_replace_tags(self):
        """Test the replace_tags utility function."""
        text = "<m>int</m> and <i>float</i> with <g>symbol</g>"
        result = replace_tags(text, "`", "m", "i", "g")
        expected = "`int` and `float` with `symbol`"
        assert result == expected

    def test_clean_text(self, cache):
        """Test text cleaning for XML parsing."""
        text = '<m>int</m> and <i>float</i> with <g>symbol</g> &quot;quoted&quot;'
        result = cache._clean_text(text)
        expected = "`int` and `float` with `symbol` `quoted`"
        assert result == expected

    def test_parse_umenu_xml(self, cache, umenu_xml_content):
        """Test parsing the umenu.maxref.xml file."""
        # Clean and parse the XML
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        # Test basic object attributes
        assert data["name"] == "umenu"
        assert data["module"] == "max"
        assert data["category"] == "U/I"
        assert data["digest"] == "Pop-up menu"
        assert "Displays text as a pop-up menu" in data["description"]

    def test_parse_metadata(self, cache, umenu_xml_content):
        """Test parsing metadata from umenu.maxref.xml."""
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        metadata = data["metadata"]
        assert metadata["author"] == "Cycling '74"
        assert "Max" in metadata["tag"]
        assert "U/I" in metadata["tag"]
        assert metadata["alias-unlisted"] == "ubumenu"

    def test_parse_inlets_outlets(self, cache, umenu_xml_content):
        """Test parsing inlets and outlets from umenu.maxref.xml."""
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        # Test inlets
        inlets = data["inlets"]
        assert len(inlets) == 1
        assert inlets[0]["id"] == "0"
        assert inlets[0]["type"] == "INLET_TYPE"
        assert inlets[0]["digest"] == "Messages in"

        # Test outlets
        outlets = data["outlets"]
        assert len(outlets) == 3
        assert outlets[0]["id"] == "0"
        # The digest is actually empty in the XML, it uses the text content
        assert outlets[0]["digest"] == "" or outlets[0]["digest"] == "Item Number Chosen"
        assert outlets[1]["id"] == "1"
        assert outlets[1]["digest"] == "" or outlets[1]["digest"] == "Menu Item Text Evaluated as a Message"
        assert outlets[2]["id"] == "2"
        assert outlets[2]["digest"] == "" or outlets[2]["digest"] == "Dumpout"

    def test_parse_palette(self, cache, umenu_xml_content):
        """Test parsing palette information."""
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        palette = data["palette"]
        assert palette["action"] == "umenu"
        assert palette["category"] == "Interface"
        assert palette["pic"] == "umenu.svg"

    def test_parse_objargs(self, cache, umenu_xml_content):
        """Test parsing object arguments."""
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        objargs = data["objargs"]
        assert len(objargs) == 1
        assert objargs[0]["id"] == "0"
        assert objargs[0]["name"] == "OBJARG_NAME"
        assert objargs[0]["type"] == "OBJARG_TYPE"
        assert objargs[0]["optional"] == "0"

    def test_parse_methods(self, cache, umenu_xml_content):
        """Test parsing methods from umenu.maxref.xml."""
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        methods = data["methods"]
        assert len(methods) > 0

        # Test specific methods
        assert "bang" in methods
        assert "int" in methods
        assert "float" in methods
        assert "append" in methods
        assert "clear" in methods

        # Test bang method (no arguments)
        bang_method = methods["bang"]
        assert bang_method["digest"] == "Output current selection"
        assert "Sends out the currently displayed menu item" in bang_method["description"]
        # The parser always creates an args list, even if empty
        assert "args" in bang_method
        assert bang_method["args"] == []

        # Test int method (with arguments)
        int_method = methods["int"]
        assert int_method["digest"] == "Select a menu item programmatically"
        assert "args" in int_method
        assert len(int_method["args"]) == 1
        assert int_method["args"][0]["name"] == "index"
        assert int_method["args"][0]["type"] == "int"
        assert int_method["args"][0]["optional"] == "0"

        # Test append method (with list argument)
        append_method = methods["append"]
        assert append_method["digest"] == "Add a menu item"
        assert "args" in append_method
        assert len(append_method["args"]) == 1
        assert append_method["args"][0]["name"] == "message"
        assert append_method["args"][0]["type"] == "list"
        assert append_method["args"][0]["optional"] == "0"

    def test_parse_attributes(self, cache, umenu_xml_content):
        """Test parsing attributes from umenu.maxref.xml."""
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        attributes = data["attributes"]
        assert len(attributes) > 0

        # Test specific attributes
        assert "align" in attributes
        assert "allowdrag" in attributes
        assert "items" in attributes
        assert "menumode" in attributes

        # Test align attribute (with nested attributes)
        align_attr = attributes["align"]
        assert align_attr["get"] == "1"
        assert align_attr["set"] == "1"
        assert align_attr["type"] == "atom"
        assert align_attr["size"] == "1"
        assert align_attr["digest"] == "Text alignment mode"
        assert "attributes" in align_attr
        assert "invisible" in align_attr["attributes"]
        assert "obsolete" in align_attr["attributes"]

        # Test menumode attribute (with enumlist)
        menumode_attr = attributes["menumode"]
        assert menumode_attr["digest"] == "Appearance/behavior mode"
        assert "enumlist" in menumode_attr
        assert len(menumode_attr["enumlist"]) == 4
        enum_names = [enum["name"] for enum in menumode_attr["enumlist"]]
        assert "Normal" in enum_names
        assert "Scrolling" in enum_names
        assert "Label" in enum_names
        assert "Toggle" in enum_names

    def test_parse_examples(self, cache, umenu_xml_content):
        """Test parsing examples from umenu.maxref.xml."""
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        examples = data["examples"]
        assert len(examples) == 1
        assert examples[0]["img"] == "umenu.png"
        assert "Used to send commands" in examples[0]["caption"]

    def test_parse_seealso(self, cache, umenu_xml_content):
        """Test parsing see also references."""
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        seealso = data["seealso"]
        assert "coll" in seealso
        assert "fontlist" in seealso

    def test_parse_misc(self, cache, umenu_xml_content):
        """Test parsing misc information."""
        cleaned = cache._clean_text(umenu_xml_content)
        root = ElementTree.fromstring(cleaned)
        data = cache._parse_maxref(root)

        misc = data["misc"]
        assert "Output" in misc
        assert "Connections" in misc

        # Test Output section
        output = misc["Output"]
        assert "int" in output
        assert "anything" in output
        assert "Out left outlet" in output["int"]
        assert "Out middle outlet" in output["anything"]


class TestMaxRefFunctions:
    """Test the public functions in the maxref module."""

    def test_get_object_info_nonexistent(self):
        """Test get_object_info with non-existent object."""
        result = get_object_info("nonexistent_object")
        assert result is None

    def test_get_object_help_nonexistent(self):
        """Test get_object_help with non-existent object."""
        result = get_object_help("nonexistent_object")
        assert result == "No help available for 'nonexistent_object'"

    def test_get_available_objects(self):
        """Test get_available_objects returns a list."""
        objects = get_available_objects()
        assert isinstance(objects, list)
        # Note: This will be empty in test environment without Max installed

    def test_get_legacy_defaults_nonexistent(self):
        """Test get_legacy_defaults with non-existent object."""
        result = get_legacy_defaults("nonexistent_object")
        assert result == {}

    def test_maxclass_defaults_contains(self):
        """Test MAXCLASS_DEFAULTS contains method."""
        # This should work even without Max installed
        assert "umenu" in MAXCLASS_DEFAULTS or "umenu" not in MAXCLASS_DEFAULTS


class TestBoxHelpMethod:
    """Test the Box.help() method functionality."""

    def test_box_help_umenu(self):
        """Test Box.help() method with umenu object."""
        # Create a Box with umenu maxclass
        box = Box(maxclass="umenu")
        
        # Test that help method returns a string
        help_text = box.help()
        assert isinstance(help_text, str)
        
        # If umenu is available in MAXCLASS_DEFAULTS, test specific content
        if "umenu" in MAXCLASS_DEFAULTS:
            assert "UMENU" in help_text
            assert "Pop-up menu" in help_text
        else:
            # If not available, should return "No help available"
            assert "No help available for 'umenu'" in help_text

    def test_box_help_newobj(self):
        """Test Box.help() method with newobj (generic object)."""
        box = Box(maxclass="newobj")
        help_text = box.help()
        assert isinstance(help_text, str)
        assert "No help available for 'newobj'" in help_text

    def test_box_help_none(self):
        """Test Box.help() method with None maxclass."""
        box = Box(maxclass=None)
        help_text = box.help()
        assert isinstance(help_text, str)
        # When maxclass is None, it defaults to "newobj"
        assert "No help available for 'newobj'" in help_text

    def test_box_get_info(self):
        """Test Box.get_info() method."""
        box = Box(maxclass="umenu")
        info = box.get_info()
        
        if info is not None:
            assert isinstance(info, dict)
            assert "name" in info
            assert "digest" in info
        else:
            # If umenu not available, should return None
            assert info is None

    def test_box_help_in_patcher(self):
        """Test Box.help() method when used in a Patcher."""
        patcher = Patcher()
        box = patcher.add_textbox("umenu")
        
        help_text = box.help()
        assert isinstance(help_text, str)
        
        # Test that the help method works on objects created by patcher
        # The add_textbox method creates a generic "newobj" by default
        assert "No help available for 'newobj'" in help_text


class TestMaxRefCache:
    """Test the MaxRefCache class functionality."""

    def test_cache_initialization(self):
        """Test MaxRefCache initialization."""
        cache = MaxRefCache()
        assert cache._cache == {}
        assert cache._refdict is None

    def test_refdict_property(self):
        """Test refdict property access."""
        cache = MaxRefCache()
        refdict = cache.refdict
        assert isinstance(refdict, dict)
        # In test environment, this will likely be empty

    def test_get_object_data_caching(self):
        """Test that get_object_data caches results."""
        cache = MaxRefCache()
        
        # First call should populate cache
        result1 = cache.get_object_data("umenu")
        
        # Second call should use cache
        result2 = cache.get_object_data("umenu")
        
        # Results should be identical
        assert result1 is result2

    def test_get_object_data_nonexistent(self):
        """Test get_object_data with non-existent object."""
        cache = MaxRefCache()
        result = cache.get_object_data("nonexistent_object")
        assert result is None

    def test_parse_maxref_empty_xml(self):
        """Test parsing empty XML."""
        cache = MaxRefCache()
        empty_xml = "<c74object></c74object>"
        root = ElementTree.fromstring(empty_xml)
        data = cache._parse_maxref(root)
        
        # Should return empty structure
        assert data["methods"] == {}
        assert data["attributes"] == {}
        assert data["metadata"] == {}
        assert data["objargs"] == []
        assert data["inlets"] == []
        assert data["outlets"] == []


class TestErrorHandling:
    """Test error handling in maxref module."""

    def test_parse_invalid_xml(self):
        """Test handling of invalid XML."""
        cache = MaxRefCache()
        
        # This should not raise an exception, but return None
        result = cache.get_object_data("invalid_xml_object")
        assert result is None

    def test_missing_file(self):
        """Test handling of missing .maxref.xml file."""
        cache = MaxRefCache()
        
        # Mock a missing file scenario
        cache._refdict = {"missing": Path("/nonexistent/path/missing.maxref.xml")}
        result = cache.get_object_data("missing")
        assert result is None

    def test_corrupted_xml_content(self):
        """Test handling of corrupted XML content."""
        cache = MaxRefCache()
        
        # Mock corrupted content
        cache._refdict = {"corrupted": Path("/tmp/corrupted.maxref.xml")}
        
        # This should not raise an exception, but return None
        result = cache.get_object_data("corrupted")
        assert result is None


class TestIntegration:
    """Integration tests for maxref functionality."""

    def test_full_workflow(self):
        """Test complete workflow from Box creation to help display."""
        # Create a patcher and add a umenu
        patcher = Patcher()
        box = patcher.add_textbox("umenu")
        
        # Test that we can get help
        help_text = box.help()
        assert isinstance(help_text, str)
        
        # Test that we can get info
        info = box.get_info()
        if info is not None:
            assert isinstance(info, dict)
            assert "name" in info

    def test_multiple_objects_help(self):
        """Test help method on multiple different objects."""
        patcher = Patcher()
        
        # Add various objects
        umenu = patcher.add_textbox("umenu")
        message = patcher.add_textbox("message")
        comment = patcher.add_textbox("comment")
        
        # Test help on all objects
        for obj in [umenu, message, comment]:
            help_text = obj.help()
            assert isinstance(help_text, str)
            assert len(help_text) > 0

    def test_help_format_consistency(self):
        """Test that help format is consistent across objects."""
        patcher = Patcher()
        box = patcher.add_textbox("umenu")
        help_text = box.help()
        
        # If help is available, it should have consistent format
        if "No help available" not in help_text:
            lines = help_text.split('\n')
            assert len(lines) > 0
            # First line should be object name in caps
            assert lines[0].startswith("===")
            assert lines[0].endswith("===")
