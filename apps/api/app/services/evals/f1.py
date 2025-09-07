def f1_token(hyp: str, ref: str) -> float:
    hyp_set = set(hyp.lower().split())
    ref_set = set(ref.lower().split())
    if not hyp_set or not ref_set:
        return 0.0
    tp = len(hyp_set & ref_set)
    precision = tp / len(hyp_set)
    recall = tp / len(ref_set)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
