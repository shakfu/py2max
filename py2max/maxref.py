"""maxref.py - Dynamic Max object information using .maxref.xml files"""

import platform
from pathlib import Path
from textwrap import fill
from xml.etree import ElementTree
from typing import Dict, Any, Optional, List

from .common import Rect


def replace_tags(text: str, sub: str, *tags: str) -> str:
    """Replace XML tags with substitution string"""
    for tag in tags:
        text = text.replace(f"<{tag}>", sub).replace(f"</{tag}>", sub)
    return text


class MaxRefCache:
    """Cache for parsed MaxRef data"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._refdict: Optional[Dict[str, Path]] = None

    @property
    def refdict(self) -> Dict[str, Path]:
        """Get dictionary of available .maxref.xml files"""
        if self._refdict is None:
            self._refdict = self._get_refdict()
        return self._refdict

    def _get_refpages(self) -> Optional[Path]:
        """Find Max refpages directory"""
        if platform.system() == "Darwin":
            for p in Path("/Applications").glob("**/Max.app"):
                if "Ableton" not in str(p):
                    refpages_path = p / "Contents/Resources/C74/docs/refpages"
                    if refpages_path.exists():
                        return refpages_path
        return None

    def _get_refdict(self) -> Dict[str, Path]:
        """Build dictionary of all available .maxref.xml files"""
        refdict = {}
        refpages = self._get_refpages()
        if refpages:
            for prefix in ["jit", "max", "msp", "m4l"]:
                ref_dir = refpages / f"{prefix}-ref"
                if ref_dir.exists():
                    for f in ref_dir.iterdir():
                        if f.name.endswith(".maxref.xml"):
                            name = f.name.replace(".maxref.xml", "")
                            refdict[name] = f
        return refdict

    def _clean_text(self, text: str) -> str:
        """Clean XML text for parsing"""
        backtick = "`"
        return replace_tags(text, backtick, "m", "i", "g", "o", "at").replace(
            "&quot;", backtick
        )

    def get_object_data(self, name: str) -> Optional[Dict[str, Any]]:
        """Get parsed data for Max object by name"""
        if name in self._cache:
            return self._cache[name]

        if name not in self.refdict:
            return None

        try:
            # Parse the .maxref.xml file
            filename = self.refdict[name]
            cleaned = self._clean_text(filename.read_text())
            root = ElementTree.fromstring(cleaned)

            data = self._parse_maxref(root)
            self._cache[name] = data
            return data
        except Exception:
            # If parsing fails, return None
            return None

    def _parse_maxref(self, root: ElementTree.Element) -> Dict[str, Any]:
        """Parse a .maxref.xml root element into structured data"""
        data: Dict[str, Any] = {
            "methods": {},
            "attributes": {},
            "metadata": {},
            "objargs": [],
            "palette": {},
            "parameter": {},
            "examples": [],
            "seealso": [],
            "misc": {},
        }

        # Basic info
        data.update(root.attrib)

        # Ensure complex fields maintain their proper types after update
        if not isinstance(data.get("methods"), dict):
            data["methods"] = {}
        if not isinstance(data.get("attributes"), dict):
            data["attributes"] = {}
        if not isinstance(data.get("metadata"), dict):
            data["metadata"] = {}
        if not isinstance(data.get("objargs"), list):
            data["objargs"] = []
        if not isinstance(data.get("palette"), dict):
            data["palette"] = {}
        if not isinstance(data.get("parameter"), dict):
            data["parameter"] = {}
        if not isinstance(data.get("examples"), list):
            data["examples"] = []
        if not isinstance(data.get("seealso"), list):
            data["seealso"] = []
        if not isinstance(data.get("misc"), dict):
            data["misc"] = {}

        digest_elem = root.find("digest")
        if digest_elem is not None and digest_elem.text:
            data["digest"] = digest_elem.text.strip()

        desc_elem = root.find("description")
        if desc_elem is not None and desc_elem.text:
            data["description"] = desc_elem.text.strip()

        # Extract all sections
        self._extract_metadata(root, data)
        self._extract_inlets_outlets(root, data)
        self._extract_palette(root, data)
        self._extract_objargs(root, data)
        self._extract_parameter(root, data)
        self._extract_methods(root, data)
        self._extract_attributes(root, data)
        self._extract_examples(root, data)
        self._extract_seealso(root, data)
        self._extract_misc(root, data)

        return data

    def _extract_metadata(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract metadata information"""
        metadatalist = root.find("metadatalist")
        if metadatalist is not None:
            for metadata in metadatalist.findall("metadata"):
                name = metadata.get("name")
                if name and metadata.text:
                    if name in data["metadata"]:
                        # Handle multiple entries (like multiple tags)
                        if not isinstance(data["metadata"][name], list):
                            data["metadata"][name] = [data["metadata"][name]]
                        data["metadata"][name].append(metadata.text.strip())
                    else:
                        data["metadata"][name] = metadata.text.strip()

    def _extract_inlets_outlets(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract inlet and outlet information"""
        data["inlets"] = []
        inletlist = root.find("inletlist")
        if inletlist is not None:
            for inlet in inletlist.findall("inlet"):
                inlet_data = dict(inlet.attrib)
                digest_elem = inlet.find("digest")
                if digest_elem is not None and digest_elem.text:
                    inlet_data["digest"] = digest_elem.text.strip()
                desc_elem = inlet.find("description")
                if desc_elem is not None and desc_elem.text:
                    inlet_data["description"] = desc_elem.text.strip()
                data["inlets"].append(inlet_data)

        data["outlets"] = []
        outletlist = root.find("outletlist")
        if outletlist is not None:
            for outlet in outletlist.findall("outlet"):
                outlet_data = dict(outlet.attrib)
                digest_elem = outlet.find("digest")
                if digest_elem is not None and digest_elem.text and outlet.text:
                    outlet_data["digest"] = outlet_data.get(
                        "digest", outlet.text.strip()
                    )
                desc_elem = outlet.find("description")
                if desc_elem is not None and desc_elem.text:
                    outlet_data["description"] = desc_elem.text.strip()
                data["outlets"].append(outlet_data)

    def _extract_palette(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract palette information"""
        palette = root.find("palette")
        if palette is not None:
            data["palette"] = dict(palette.attrib)

    def _extract_objargs(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract object arguments"""
        objarglist = root.find("objarglist")
        if objarglist is not None:
            for objarg in objarglist.findall("objarg"):
                arg_data = dict(objarg.attrib)
                digest_elem = objarg.find("digest")
                if digest_elem is not None and digest_elem.text:
                    arg_data["digest"] = digest_elem.text.strip()
                desc_elem = objarg.find("description")
                if desc_elem is not None and desc_elem.text:
                    arg_data["description"] = desc_elem.text.strip()
                data["objargs"].append(arg_data)

    def _extract_parameter(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract parameter information"""
        parameter = root.find("parameter")
        if parameter is not None:
            data["parameter"] = dict(parameter.attrib)

    def _extract_examples(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract example information"""
        examplelist = root.find("examplelist")
        if examplelist is not None:
            for example in examplelist.findall("example"):
                data["examples"].append(dict(example.attrib))

    def _extract_seealso(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract see also references"""
        seealsolist = root.find("seealsolist")
        if seealsolist is not None:
            for seealso in seealsolist.findall("seealso"):
                name = seealso.get("name")
                if name:
                    data["seealso"].append(name)

    def _extract_misc(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract misc information like Output and Connections"""
        for misc in root.findall("misc"):
            misc_name = misc.get("name")
            if misc_name:
                data["misc"][misc_name] = {}
                for entry in misc.findall("entry"):
                    entry_name = entry.get("name")
                    if entry_name:
                        desc_elem = entry.find("description")
                        if desc_elem is not None and desc_elem.text:
                            data["misc"][misc_name][entry_name] = desc_elem.text.strip()

    def _extract_attributes(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract attribute information with full nested structure"""
        attributelist = root.find("attributelist")
        if attributelist is not None:
            for attr in attributelist.findall("attribute"):
                name = attr.get("name")
                if name:
                    # Build attr_data properly, avoiding conflicts with nested structures
                    attr_data: Dict[str, Any] = dict(attr.attrib)

                    # Extract digest
                    digest_elem = attr.find("digest")
                    if digest_elem is not None and digest_elem.text:
                        attr_data["digest"] = digest_elem.text.strip()

                    # Extract description
                    desc_elem = attr.find("description")
                    if desc_elem is not None and desc_elem.text:
                        attr_data["description"] = desc_elem.text.strip()

                    # Extract nested attributelist (meta-attributes)
                    nested_attrs = attr.find("attributelist")
                    if nested_attrs is not None:
                        # Ensure attributes is a dict (in case it was set as a string in XML)
                        attr_data["attributes"] = {}
                        for nested_attr in nested_attrs.findall("attribute"):
                            nested_name = nested_attr.get("name")
                            if nested_name:
                                nested_data = dict(nested_attr.attrib)
                                attr_data["attributes"][nested_name] = nested_data

                    # Extract enumlist if present
                    enumlist = attr.find(".//enumlist")
                    if enumlist is not None:
                        # Ensure enumlist is a list (in case it was set as a string in XML)
                        attr_data["enumlist"] = []
                        for enum in enumlist.findall("enum"):
                            enum_data = dict(enum.attrib)
                            digest_elem = enum.find("digest")
                            if digest_elem is not None and digest_elem.text:
                                enum_data["digest"] = digest_elem.text.strip()
                            desc_elem = enum.find("description")
                            if desc_elem is not None and desc_elem.text:
                                enum_data["description"] = desc_elem.text.strip()
                            attr_data["enumlist"].append(enum_data)

                    data["attributes"][name] = attr_data

    def _extract_methods(self, root: ElementTree.Element, data: Dict[str, Any]):
        """Extract method information with full argument and attribute support"""
        methodlist = root.find("methodlist")
        if methodlist is not None:
            for method in methodlist.findall("method"):
                name = method.get("name")
                if name:
                    # Build method_data properly, avoiding conflicts with nested structures
                    method_data: Dict[str, Any] = dict(method.attrib)

                    # Extract arguments
                    arglist = method.find("arglist")
                    if arglist is not None:
                        # Ensure args is a list (in case it was set as a string in XML)
                        method_data["args"] = []
                        for arg in arglist.findall("arg"):
                            method_data["args"].append(dict(arg.attrib))

                        # Handle argument groups
                        for arggroup in arglist.findall("arggroup"):
                            group_attrs = dict(arggroup.attrib)
                            for arg in arggroup.findall("arg"):
                                arg_data = dict(arg.attrib)
                                arg_data.update(group_attrs)  # Add group attributes
                                method_data["args"].append(arg_data)

                    # Extract digest
                    digest_elem = method.find("digest")
                    if digest_elem is not None and digest_elem.text:
                        method_data["digest"] = digest_elem.text.strip()

                    # Extract description
                    desc_elem = method.find("description")
                    if desc_elem is not None and desc_elem.text:
                        method_data["description"] = desc_elem.text.strip()

                    # Extract nested attributelist (method attributes like 'introduced')
                    nested_attrs = method.find("attributelist")
                    if nested_attrs is not None:
                        # Ensure attributes is a dict (in case it was set as a string in XML)
                        method_data["attributes"] = {}
                        for nested_attr in nested_attrs.findall("attribute"):
                            nested_name = nested_attr.get("name")
                            if nested_name:
                                nested_data = dict(nested_attr.attrib)
                                method_data["attributes"][nested_name] = nested_data

                    data["methods"][name] = method_data


# Global cache instance
_maxref_cache = MaxRefCache()


def get_object_info(name: str) -> Optional[Dict[str, Any]]:
    """Get information about a Max object from its .maxref.xml file

    Args:
        name: Max object name (e.g., 'umenu', 'cycle~', 'gain~')

    Returns:
        Dictionary with complete object information or None if not found
    """
    return _maxref_cache.get_object_data(name)


def get_object_help(name: str) -> str:
    """Get formatted help text for a Max object

    Args:
        name: Max object name

    Returns:
        Formatted help text string
    """
    data = get_object_info(name)
    if not data:
        return f"No help available for '{name}'"

    lines = []
    lines.append(f"=== {name.upper()} ===")

    if "digest" in data:
        lines.append(f"Digest: {data['digest']}")

    if "description" in data:
        lines.append("\nDescription:")
        lines.append(fill(data["description"], width=70, subsequent_indent="  "))

    if data.get("inlets"):
        lines.append("\nInlets:")
        for i, inlet in enumerate(data["inlets"]):
            inlet_info = f"  {inlet.get('id', i)}: {inlet.get('type', 'unknown')}"
            if "digest" in inlet:
                inlet_info += f" - {inlet['digest']}"
            lines.append(inlet_info)

    if data.get("outlets"):
        lines.append("\nOutlets:")
        for i, outlet in enumerate(data["outlets"]):
            outlet_info = f"  {outlet.get('id', i)}: {outlet.get('type', 'unknown')}"
            if "digest" in outlet:
                outlet_info += f" - {outlet['digest']}"
            lines.append(outlet_info)

    # Show some key methods
    methods = data.get("methods", {})
    if methods:
        method_names = list(methods.keys())[:5]  # Show first 5 methods
        lines.append(f"\nKey Methods: {', '.join(method_names)}")
        if len(methods) > 5:
            lines.append(f"  (and {len(methods) - 5} more...)")

    if data.get("seealso"):
        lines.append(f"\nSee Also: {', '.join(data['seealso'])}")

    return "\n".join(lines)


def get_available_objects() -> List[str]:
    """Get list of all available Max objects with .maxref.xml files"""
    return sorted(_maxref_cache.refdict.keys())


# Legacy compatibility - generate defaults from .maxref.xml when available
def get_legacy_defaults(name: str) -> Dict[str, Any]:
    """Get legacy-compatible defaults for a Max object

    This function extracts basic information needed for backwards compatibility
    with the old MAXCLASS_DEFAULTS structure.
    """
    data = get_object_info(name)
    if not data:
        return {}

    # Only set maxclass to the object name for objects that had explicit
    # maxclass entries in the legacy database. All other objects should
    # use "newobj" as maxclass (handled by fallback in core.py)
    from .maxclassdb import MAXCLASS_DEFAULTS as LEGACY_DEFAULTS

    defaults: Dict[str, Any] = {}
    if name in LEGACY_DEFAULTS:
        defaults["maxclass"] = name

    # Extract inlet/outlet counts and types
    inlets = data.get("inlets", [])
    outlets = data.get("outlets", [])

    if inlets:
        defaults["numinlets"] = len(inlets)

    if outlets:
        defaults["numoutlets"] = len(outlets)
        outlet_types = []
        for outlet in outlets:
            outlet_type = outlet.get("type", "").replace("OUTLET_TYPE", "")
            if not outlet_type:
                outlet_type = ""
            outlet_types.append(outlet_type)
        if outlet_types:
            defaults["outlettype"] = outlet_types

    # Set a default patching rect - this could be improved by analyzing
    # the palette info or other attributes in the future
    defaults["patching_rect"] = Rect(x=0.0, y=0.0, w=60.0, h=22.0)

    return defaults


def validate_connection(
    src_maxclass: str, src_outlet: int, dst_maxclass: str, dst_inlet: int
) -> tuple[bool, str]:
    """Validate a connection between two Max objects using maxref data.

    Args:
        src_maxclass: Source object's maxclass
        src_outlet: Source outlet index (0-based)
        dst_maxclass: Destination object's maxclass
        dst_inlet: Destination inlet index (0-based)

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Get object information
    src_info = get_object_info(src_maxclass)
    dst_info = get_object_info(dst_maxclass)

    # If we don't have maxref data, allow connection (backwards compatibility)
    if not src_info or not dst_info:
        return True, ""

    # Check source outlet exists
    src_outlets = src_info.get("outlets", [])
    if src_outlets and src_outlet >= len(src_outlets):
        return (
            False,
            f"Object '{src_maxclass}' only has {len(src_outlets)} outlet(s), cannot connect from outlet {src_outlet}",
        )

    # Check destination inlet exists
    dst_inlets = dst_info.get("inlets", [])
    if dst_inlets and dst_inlet >= len(dst_inlets):
        return (
            False,
            f"Object '{dst_maxclass}' only has {len(dst_inlets)} inlet(s), cannot connect to inlet {dst_inlet}",
        )

    # Type checking (optional - could be enhanced)
    if (
        src_outlets
        and dst_inlets
        and src_outlet < len(src_outlets)
        and dst_inlet < len(dst_inlets)
    ):
        src_outlet_type = src_outlets[src_outlet].get("type", "")
        dst_inlet_type = dst_inlets[dst_inlet].get("type", "")

        # Basic type compatibility checking
        if src_outlet_type and dst_inlet_type:
            # Signal connections
            if "signal" in src_outlet_type and "signal" not in dst_inlet_type:
                return (
                    False,
                    f"Cannot connect signal outlet from '{src_maxclass}' to non-signal inlet of '{dst_maxclass}'",
                )

            # Could add more sophisticated type checking here

    return True, ""


def get_inlet_count(maxclass: str) -> Optional[int]:
    """Get the number of inlets for a Max object.

    Args:
        maxclass: The Max object class name

    Returns:
        Number of inlets or None if unknown
    """
    info = get_object_info(maxclass)
    if info and "inlets" in info:
        return len(info["inlets"])
    return None


def get_outlet_count(maxclass: str) -> Optional[int]:
    """Get the number of outlets for a Max object.

    Args:
        maxclass: The Max object class name

    Returns:
        Number of outlets or None if unknown
    """
    info = get_object_info(maxclass)
    if info and "outlets" in info:
        return len(info["outlets"])
    return None


def get_inlet_types(maxclass: str) -> List[str]:
    """Get the inlet types for a Max object.

    Args:
        maxclass: The Max object class name

    Returns:
        List of inlet type strings
    """
    info = get_object_info(maxclass)
    if info and "inlets" in info:
        return [inlet.get("type", "") for inlet in info["inlets"]]
    return []


def get_outlet_types(maxclass: str) -> List[str]:
    """Get the outlet types for a Max object.

    Args:
        maxclass: The Max object class name

    Returns:
        List of outlet type strings
    """
    info = get_object_info(maxclass)
    if info and "outlets" in info:
        return [outlet.get("type", "") for outlet in info["outlets"]]
    return []


# Build a compatibility layer for the old MAXCLASS_DEFAULTS
class MaxClassDefaults:
    """Compatibility wrapper that provides legacy MAXCLASS_DEFAULTS interface
    while using dynamic .maxref.xml loading"""

    def __contains__(self, key: str) -> bool:
        """Check if object exists in .maxref.xml files or legacy defaults"""
        from .maxclassdb import MAXCLASS_DEFAULTS as LEGACY_DEFAULTS

        return key in LEGACY_DEFAULTS or get_object_info(key) is not None

    def __getitem__(self, key: str) -> Dict[str, Any]:
        """Get defaults for an object, preferring legacy, falling back to .maxref.xml"""
        from .maxclassdb import MAXCLASS_DEFAULTS as LEGACY_DEFAULTS

        if key in LEGACY_DEFAULTS:
            return LEGACY_DEFAULTS[key]

        # Try to get from .maxref.xml
        legacy_defaults = get_legacy_defaults(key)
        if legacy_defaults:
            return legacy_defaults

        raise KeyError(f"No defaults found for maxclass '{key}'")

    def get(self, key: str, default=None):
        """Get defaults with fallback"""
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        """Get all available keys"""
        from .maxclassdb import MAXCLASS_DEFAULTS as LEGACY_DEFAULTS

        legacy_keys = set(LEGACY_DEFAULTS.keys())
        maxref_keys = set(get_available_objects())
        return legacy_keys | maxref_keys


# Create the compatibility instance
MAXCLASS_DEFAULTS = MaxClassDefaults()
