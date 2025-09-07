from prompts.define import make_draft

def test_make_draft_includes_goal():
    goal = "제품 리뷰 요약"
    draft = make_draft(goal)
    assert "제품 리뷰 요약" in draft
    assert "# 출력 형식" in draft
