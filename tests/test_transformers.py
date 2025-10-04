from py2max import Patcher
from py2max.transformers import (
    add_comment_transform,
    compose,
    optimize_layout,
    run_pipeline,
    set_font_size,
)


def build_patch() -> Patcher:
    patcher = Patcher()
    osc = patcher.add_textbox("cycle~ 440")
    gain = patcher.add_textbox("gain~")
    dac = patcher.add_textbox("ezdac~")
    patcher.link(osc, gain)
    patcher.link(gain, dac)
    patcher.link(gain, dac, inlet=1)
    return patcher


def test_run_pipeline_applies_transforms():
    patcher = build_patch()
    transformed = run_pipeline(
        patcher,
        [
            set_font_size(20.0),
            add_comment_transform("Auto", pos="below"),
        ],
    )

    assert transformed.default_fontsize == 20.0
    comments = [box for box in transformed._boxes if box.maxclass == "comment"]
    assert comments
    assert all(comment.text == "Auto" for comment in comments)


def test_compose_matches_pipeline():
    patcher = build_patch()
    pipeline = compose([set_font_size(16.0), optimize_layout("grid")])
    transformed = pipeline(patcher)

    assert transformed.default_fontsize == 16.0
    assert transformed._layout_mgr is not None


def test_optimize_layout_transform_updates_layout():
    patcher = build_patch()
    transformed = optimize_layout(layout="vertical", flow_direction="vertical")(patcher)

    assert transformed._layout_mgr is not None
    assert getattr(transformed._layout_mgr, "flow_direction", "") == "vertical"

