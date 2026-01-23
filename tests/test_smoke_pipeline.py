import subprocess
import sys
from pathlib import Path

def test_train_and_score_smoke(tmp_path):
    # tiny sample log file
    p = tmp_path / "sample.log"
    p.write_text("INFO ok\nERROR CrashLoopBackOff\n", encoding="utf-8")

    env = dict(**{"MLFLOW_TRACKING_URI": "file:./mlruns"})
    subprocess.check_call([sys.executable, "-m", "src.pipeline.train", "--data", str(p), "--experiment", "ci-exp"], env=env)
    subprocess.check_call([sys.executable, "-m", "src.pipeline.score", "--data", str(p), "--experiment", "ci-exp", "--topk", "1"], env=env)
    assert Path("outputs/anomalies.csv").exists()
