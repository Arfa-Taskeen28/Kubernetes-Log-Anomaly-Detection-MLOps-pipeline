import argparse
import json
from pathlib import Path
import mlflow
from collections import Counter

from src.lib.drift import vocab_drift_proxy, token_stats

def _load_latest_train_tokens(exp_name: str) -> Counter:
    client = mlflow.tracking.MlflowClient()
    exp = client.get_experiment_by_name(exp_name)
    if exp is None:
        raise RuntimeError(f"Experiment not found: {exp_name}.")

    runs = client.search_runs([exp.experiment_id], order_by=["attributes.start_time DESC"], max_results=50)
    train_runs = [r for r in runs if r.info.run_name == "train"]
    if not train_runs:
        raise RuntimeError("No train run found. Run train first.")

    run_id = train_runs[0].info.run_id
    tok_local = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="train_tokens.json")

    items = json.loads(Path(tok_local).read_text(encoding="utf-8"))
    return Counter({k: int(v) for k, v in items})

def _load_latest_score_summary(exp_name: str) -> dict:
    client = mlflow.tracking.MlflowClient()
    exp = client.get_experiment_by_name(exp_name)
    if exp is None:
        raise RuntimeError(f"Experiment not found: {exp_name}.")

    runs = client.search_runs([exp.experiment_id], order_by=["attributes.start_time DESC"], max_results=50)
    score_runs = [r for r in runs if r.info.run_name == "score"]
    if not score_runs:
        raise RuntimeError("No score run found. Run score first.")

    run_id = score_runs[0].info.run_id
    summ_local = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="summary.json")
    return json.loads(Path(summ_local).read_text(encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", default="k8s-log-anomaly")
    ap.add_argument("--out", default="outputs/monitor.json")
    args = ap.parse_args()

    mlflow.set_experiment(args.experiment)

    train_tokens = _load_latest_train_tokens(args.experiment)
    summary = _load_latest_score_summary(args.experiment)

    # Lightweight monitoring output (you can extend later)
    monitor = {
        "anomaly_rate_proxy_p95": summary.get("anomaly_rate_proxy_p95"),
        "n_lines": summary.get("n_lines"),
        "drift_note": "Token drift proxy requires scoring-time tokens; add if you persist them.",
        "recommended_threshold_policy": "Alert if anomaly_rate_proxy_p95 > baseline + 3*std over last N runs.",
    }

    Path("outputs").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(monitor, indent=2), encoding="utf-8")

    with mlflow.start_run(run_name="monitor"):
        mlflow.log_metric("anomaly_rate_proxy_p95", float(monitor["anomaly_rate_proxy_p95"]))
        mlflow.log_artifact(args.out)

    print(f"Saved: {args.out}")

if __name__ == "__main__":
    main()
