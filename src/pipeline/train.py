import argparse
import json
from pathlib import Path
import joblib
import mlflow

from src.lib.io import read_lines
from src.lib.parse import normalize
from src.lib.model import train
from src.lib.drift import token_stats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--experiment", default="k8s-log-anomaly")
    ap.add_argument("--random_state", type=int, default=42)
    args = ap.parse_args()

    mlflow.set_experiment(args.experiment)

    raw_lines = read_lines(args.data)
    lines_norm = [normalize(l) for l in raw_lines]

    with mlflow.start_run(run_name="train"):
        mlflow.log_param("model_type", "IsolationForest")
        mlflow.log_param("vectorizer", "TFIDF(1,2)")
        mlflow.log_param("random_state", args.random_state)
        mlflow.log_param("n_lines", len(lines_norm))

        art = train(lines_norm, random_state=args.random_state)

        # Save artifacts locally (optional) and to MLflow
        Path("models").mkdir(exist_ok=True)
        vec_path = "models/vectorizer.pkl"
        mdl_path = "models/isoforest.pkl"
        tok_path = "models/train_tokens.json"

        joblib.dump(art.vectorizer, vec_path)
        joblib.dump(art.model, mdl_path)

        train_tokens = token_stats(lines_norm)
        Path(tok_path).write_text(json.dumps(train_tokens.most_common(5000)), encoding="utf-8")

        mlflow.log_artifact(vec_path)
        mlflow.log_artifact(mdl_path)
        mlflow.log_artifact(tok_path)

        # Basic training distribution metric (unsupervised sanity check)
        # (We avoid leaking scoring logic here to keep it minimal.)
        mlflow.log_metric("train_lines", len(lines_norm))

    print("Training completed. Artifacts logged to MLflow.")

if __name__ == "__main__":
    main()
