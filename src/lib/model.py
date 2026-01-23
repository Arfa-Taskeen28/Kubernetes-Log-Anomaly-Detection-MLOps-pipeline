from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest

@dataclass
class AnomalyArtifacts:
    vectorizer: TfidfVectorizer
    model: IsolationForest

def train(lines_norm: list[str], random_state: int = 42) -> AnomalyArtifacts:
    vec = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=2,
        max_features=20000
    )
    X = vec.fit_transform(lines_norm)

    clf = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=random_state,
        n_jobs=-1
    )
    clf.fit(X)
    return AnomalyArtifacts(vec, clf)

def anomaly_scores(art: AnomalyArtifacts, lines_norm: list[str]) -> list[float]:
    X = art.vectorizer.transform(lines_norm)
    normality = art.model.score_samples(X)      # higher = more normal
    return (-normality).tolist()                # higher = more anomalous
