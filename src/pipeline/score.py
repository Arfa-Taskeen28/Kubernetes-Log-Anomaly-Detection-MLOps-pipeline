import argparse
import json
from pathlib import Path
import pandas as pd
import joblib
import mlflow

from src.lib.io import read_lines
from src.lib.parse import normalize
from src.lib.model import AnomalyArtifacts, anomaly_scores

def _load_latest_artifacts(exp_name: str) -> tuple[str, str, str]:
    client = mlflow.tracking.MlflowClient()
    exp = client.get_experiment_by_name(exp_name)
    if exp is None:
        raise RuntimeError(f"Experiment not found: {exp_name}. Run train first.")

    runs = client.search_runs([exp.experiment_id], order_by=["attributes.start_time DESC"], max_results=50)
    train_runs = [r for r in runs if r.info.run_name == "train"]
    if not train_runs:
        raise RuntimeError("No train run found in experiment. Run train first.")

    run_id = train_runs[0].info.run_id
    # Download artifacts to local temp dirs
    vec_local = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="vectorizer.pkl")
    mdl_local = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="isoforest.pkl")
    tok_local = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="train_tokens.json")
    return vec_local, mdl_local, tok_local

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--experiment", default="k8s-log-anomaly")
    ap.add_argument("--topk", type=int, default=50)
    ap.add_argument("--out_csv", default="outputs/anomalies.csv")
    ap.add_argument("--out_summary", default="outputs/summary.json")
    args = ap.parse_args()

    mlflow.set_experiment(args.experiment)

    raw_lines = read_lines(args.data)
    lines_norm = [normalize(l) for l in raw_lines]

    vec_path, mdl_path, _tok_path = _load_latest_artifacts(args.experiment)
    vec = joblib.load(vec_path)
    mdl = joblib.load(mdl_path)
    art = AnomalyArtifacts(vec, mdl)

    scores = anomaly_scores(art, lines_norm)

    df = pd.DataFrame({
        "line": raw_lines,
        "normalized": lines_norm,
        "anomaly_score": scores
    }).sort_values("anomaly_score", ascending=False)

    Path("outputs").mkdir(exist_ok=True)
    df.head(args.topk).to_csv(args.out_csv, index=False)

    anomaly_rate = float((df["anomaly_score"] > df["anomaly_score"].quantile(0.95)).mean())
    summary = {
        "n_lines": int(len(df)),
        "topk": int(args.topk),
        "anomaly_rate_proxy_p95": anomaly_rate,
        "max_score": float(df["anomaly_score"].max()),
        "median_score": float(df["anomaly_score"].median()),
    }
    Path(args.out_summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with mlflow.start_run(run_name="score"):
        mlflow.log_param("data", args.data)
        mlflow.log_param("topk", args.topk)
        mlflow.log_metric("anomaly_rate_proxy_p95", anomaly_rate)
        mlflow.log_artifact(args.out_csv)
        mlflow.log_artifact(args.out_summary)

    print(f"Saved: {args.out_csv}")
    print(f"Saved: {args.out_summary}")
    print(df.head(10)[["anomaly_score", "line"]].to_string(index=False))

if __name__ == "__main__":
    main()
