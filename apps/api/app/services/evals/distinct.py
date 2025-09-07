def distinct_1(text: str) -> float:
    tokens = text.split()
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)
