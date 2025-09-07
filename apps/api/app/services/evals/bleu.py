import sacrebleu

def bleu(hyp: str, ref: str) -> float:
    return sacrebleu.corpus_bleu([hyp], [[ref]]).score
