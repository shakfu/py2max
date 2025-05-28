from py2max import Patcher


def test_pydantic_basic():
    p = Patcher(path="outputs/test_pydantic_model.maxpat")
    osc = p.add("cycle~ 440")
    dac = p.add("ezdac~")
    p.link(osc, dac)
    p.link(osc, dac, inlet=1)
    p.save()

    roundtrip = Patcher.model_validate(p.model_dump(), strict=True)
    roundtrip.save_as("outputs/test_pydantic_roundtrip.maxpat")


def test_pydantic_from_file():
    simple = Patcher.from_file("tests/data/simple.maxpat")
    simple.save_as("outputs/test_pydantic_simple.maxpat")
    complex = Patcher.from_file("tests/data/complex.maxpat")
    complex.save_as("outputs/test_pydantic_complex.maxpat")
    nested = Patcher.from_file("tests/data/nested.maxpat")
    nested.save_as("outputs/test_pydantic_nested.maxpat")
