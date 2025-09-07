from prompts.edit import apply_edits

def test_apply_edits_basic():
    src = "A\nB\nC"
    edits = [{"op":"set","line":2,"text":"BB"}, {"op":"insert","line":2,"text":"X"}, {"op":"delete","line":3}]
    out = apply_edits(src, edits)
    assert out.splitlines() == ["A","X","BB"]
