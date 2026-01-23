import math
from collections import Counter

def token_stats(lines_norm: list[str]) -> Counter:
    c = Counter()
    for s in lines_norm:
        for tok in s.lower().split():
            c[tok] += 1
    return c

def vocab_drift_proxy(train_tokens: Counter, new_tokens: Counter) -> dict:
    # Fraction of token mass unseen in training (simple but defensible proxy)
    total = sum(new_tokens.values()) or 1
    unseen = sum(v for t, v in new_tokens.items() if t not in train_tokens)
    frac_unseen = unseen / total

    # Entropy proxy (optional)
    probs = [v / total for v in new_tokens.values()]
    entropy = -sum(p * math.log(p + 1e-12) for p in probs)

    return {
        "token_mass_unseen_fraction": frac_unseen,
        "token_entropy": entropy,
        "unique_tokens_new": len(new_tokens),
        "unique_tokens_train": len(train_tokens),
    }
