import os
import subprocess
import sys
from pathlib import Path

def test_train_score_monitor_smoke(tmp_path):
    os.environ["MLFLOW_TRACKING_URI"] = "file:./mlruns"

    p = tmp_path / "sample.log"
    p.write_text(
        "2026-01-01T00:00:00Z Normal Started Started container app\n"
        "2026-01-01T00:00:01Z Warning CrashLoopBackOff pod/api-abc CrashLoopBackOff\n",
        encoding="utf-8"
    )

    subprocess.check_call([sys.executable, "-m", "src.pipeline.train", "--data", str(p), "--experiment", "test-exp"])
    subprocess.check_call([sys.executable, "-m", "src.pipeline.score", "--data", str(p), "--experiment", "test-exp", "--topk", "1"])
    subprocess.check_call([sys.executable, "-m", "src.pipeline.monitor", "--experiment", "test-exp"])

    assert Path("outputs/anomalies.csv").exists()
    assert Path("outputs/summary.json").exists()
    assert Path("outputs/monitor.json").exists()
