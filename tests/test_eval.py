from prompts.eval import evaluate

def test_evaluate_sections():
    content = "# 목표\nx\n# 지시사항\nx\n# 제약조건\nx\n# 출력 형식\nx\n# 평가 기준\nx\n1) a\n- b"
    r = evaluate(content)
    assert r["score"] > 60
    assert not r["red_flags"]
