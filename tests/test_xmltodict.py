import pytest

try:
	import xmltodict
	HAS_XMLTODICT = True
except ImportError:
	HAS_XMLTODICT = False

@pytest.fixture
def xmlfile():
	content = None
	with open("tests/data/cos.maxref.xml") as f:
		content = f.read()
	return content

@pytest.mark.skipif(not HAS_XMLTODICT, reason="requires xmltodict")
def test_xmltodict(xmlfile):
	d = xmltodict.parse(xmlfile)
	root = d['c74object']
	assert root['@name'] == 'cos'
	assert root['digest'] == 'Cosine function'
