from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Iterable, Tuple
import re

try:
    from langdetect import detect
except Exception:
    detect = None

from ..models import Post


# ---------------------------------------------------------------------------
# Vocabulary (simple rule-based lists)
# ---------------------------------------------------------------------------

VIOLENT_KEYWORDS = {
    "kill",
    "killing",
    "murder",
    "attack",
    "shoot",
    "shooting",
    "bomb",
    "bombing",
    "stab",
    "stabbing",
    "genocide",
    "execute",
    "execution",
    "lynch",
    "slaughter",
    "massacre",
    "terrorist",
    "terrorism",
}

HATE_KEYWORDS = {
    "racist",
    "racism",
    "nazi",
    "nazis",
    "hitler",
    "subhuman",
    "vermin",
    "garbage",
    "retard",
    "retarded",
    "scum",
    "freaks",
    "trash",
    "animals",
}

INTENSIFIERS = {
    "very",
    "really",
    "extremely",
    "super",
    "totally",
    "literally",
    "so",
    "utterly",
    "completely",
}

THREAT_PATTERNS = [
    r"\bi[' ]?m going to (kill|hurt|beat|destroy)\b",
    r"\bi will (kill|hurt|beat|destroy)\b",
    r"\bwe should (kill|bomb|lynch|wipe out)\b",
    r"\b(deserve|deserves) to die\b",
    r"\bshould be (killed|shot|bombed|wiped out)\b",
]

THREAT_REGEXES = [re.compile(p, re.IGNORECASE) for p in THREAT_PATTERNS]
WORD_RE = re.compile(r"\w+")


# ---------------------------------------------------------------------------
# Output object
# ---------------------------------------------------------------------------


@dataclass
class PostRisk:
    post_id: str
    language: str
    score: float
    label: str
    explanation: str
    feature_values: Dict[str, float]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_text(post: Post) -> Tuple[str, str]:
    """Collect (title + body) from possible fields."""
    title = getattr(post, "title", "") or ""
    body_candidates = [
        getattr(post, "text", None),
        getattr(post, "selftext", None),
        getattr(post, "body", None),
        getattr(post, "content", None),
    ]
    body = next((b for b in body_candidates if isinstance(b, str) and b.strip()), "")
    combined = f"{title}\n{body}".strip()
    return combined, title


def _detect_language(text: str) -> str:
    if detect is None or len(text) < 20:
        return "unknown"
    try:
        return detect(text)
    except Exception:
        return "unknown"


def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text)]


def _violent_feature(tokens):
    hits = [t for t in tokens if t in VIOLENT_KEYWORDS]
    c = len(hits)
    return min(c / 3.0, 1.0), c, sorted(set(hits))


def _hate_feature(tokens):
    hits = [t for t in tokens if t in HATE_KEYWORDS]
    c = len(hits)
    return min(c / 3.0, 1.0), c, sorted(set(hits))


def _intensifier_feature(tokens):
    hits = [t for t in tokens if t in INTENSIFIERS]
    c = len(hits)
    return min(c / 3.0, 1.0), c


def _keyword_density(tokens, violent_count, hate_count):
    if not tokens:
        return 0.0
    density = (violent_count + hate_count) / len(tokens)
    return min(density / 0.1, 1.0)  # 10% keywords = max


def _threat_feature(text):
    hits = []
    for r in THREAT_REGEXES:
        for m in r.finditer(text):
            hits.append(m.group(0))
    return (1.0 if hits else 0.0), hits


def _all_caps_feature(text):
    if not text:
        return 0.0
    words = text.split()
    if not words:
        return 0.0

    def is_allcaps(w):
        letters = [c for c in w if c.isalpha()]
        return len(letters) >= 3 and all(c.isupper() for c in letters)

    caps = sum(1 for w in words if is_allcaps(w))
    ratio = caps / len(words)
    return min(ratio / 0.3, 1.0)  # 30% caps = max


def _combine(features: Dict[str, float]) -> float:
    weights = {
        "violent": 0.30,
        "hate": 0.25,
        "keyword_density": 0.15,
        "threat": 0.15,
        "all_caps": 0.10,
        "intensifiers": 0.05,
    }
    s = sum(weights[k] * features.get(k, 0.0) for k in weights)
    return max(0.0, min(s, 1.0))


def _label(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_post(post: Post) -> PostRisk:
    text, title = _extract_text(post)
    lang = _detect_language(text)
    tokens = _tokenize(text)

    violent_f, violent_c, violent_terms = _violent_feature(tokens)
    hate_f, hate_c, hate_terms = _hate_feature(tokens)
    intens_f, intens_c = _intensifier_feature(tokens)
    density_f = _keyword_density(tokens, violent_c, hate_c)
    threat_f, threat_hits = _threat_feature(text)
    caps_f = _all_caps_feature(text)

    features = {
        "violent": violent_f,
        "hate": hate_f,
        "keyword_density": density_f,
        "intensifiers": intens_f,
        "threat": threat_f,
        "all_caps": caps_f,
    }

    score = _combine(features)
    lbl = _label(score)

    # Build explanation
    parts = [
        f"language={lang}",
        f"score={score:.2f} ({lbl})",
    ]
    if violent_c:
        parts.append(f"violent={violent_c} ({', '.join(violent_terms[:5])})")
    if hate_c:
        parts.append(f"hate={hate_c} ({', '.join(hate_terms[:5])})")
    if intens_c:
        parts.append(f"intensifiers={intens_c}")
    if threat_hits:
        parts.append(f"threat=({'; '.join(threat_hits[:3])})")
    if caps_f > 0:
        parts.append(f"allcaps={caps_f:.2f}")
    if density_f > 0:
        parts.append(f"density={density_f:.2f}")
    if not (violent_c or hate_c or threat_hits):
        parts.append("no explicit harmful keywords")

    explanation = "; ".join(parts)

    pid = getattr(post, "id", "") or getattr(post, "post_id", "")

    return PostRisk(
        post_id=str(pid),
        language=lang,
        score=score,
        label=lbl,
        explanation=explanation,
        feature_values=features,
    )


def score_posts(posts: Iterable[Post]) -> List[PostRisk]:
    return [score_post(p) for p in posts]
