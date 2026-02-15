# Kubernetes & AWS EKS Log Anomaly Detection System

1.  Introduction
Modern cloud-native infrastructures such as Kubernetes and AWS Elastic Kubernetes Service (EKS) generate large volumes of heterogeneous logs originating from application workloads, system components, and control-plane events. These logs are essential for diagnosing failures, ensuring reliability, and maintaining service availability.
However, manual inspection of logs is infeasible at scale, and rule-based alerting systems often suffer from poor generalization and high false-positive rates. This motivates the use of machine learning–based anomaly detection, capable of identifying unusual log patterns that may correspond to failures, misconfigurations, or security-relevant events.
This project addresses the problem of log anomaly detection in Kubernetes environments, with a focus on system-level engineering aspects, including reproducibility, monitoring, and operational readiness.

2. Project Type and Objectives
This project is primarily **Innovation-driven**, with a strong emphasis on system design, prototyping, and evaluation, as required by the AI Systems Engineering guidelines.
Objectives:
- Design an end-to-end AI system for anomaly detection in Kubernetes/EKS logs
- Implement a reproducible MLOps batch pipeline
- Apply unsupervised machine learning to log data
- Track experiments and artifacts using MLflow
- Provide monitoring signals suitable for operational environments

3. Functiona Requirements:
- Ingest Kubernetes log data
- Normalize high-cardinality log attributes (IPs, IDs, hashes)
- Train an unsupervised anomaly detection model
- Score new logs and rank them by anomaly severity
- Produce human-readable anomaly reports

## Key Features

- Synthetic Kubernetes / EKS log generation (simulation-based)
- Log normalization to reduce high-cardinality noise
- TF-IDF feature extraction from log messages
- Isolation Forest for unsupervised anomaly detection
- Batch inference with ranked anomaly reports
- MLflow experiment tracking and artifact versioning
- Monitoring outputs for system-level analysis
- GitHub Actions CI (tests + pipeline smoke run)

## Methodology

- **Normalization** reduces noise from unique identifiers (IPs, IDs, pod hashes)
- **TF-IDF** provides a fast, interpretable vector representation for log lines
- **Isolation Forest** performs unsupervised anomaly scoring without labels
- **MLflow** provides experiment tracking and artifact versioning for reproducibility

## Repository Structure
├── data/
│ └── raw/ # generated logs
├── outputs/ # anomalies.csv, summary.json, monitor.json
├── scripts/
│ └── generate_logs.py # synthetic Kubernetes/EKS log generator
├── src/
│ ├── lib/ # parsing, modeling utilities
│ └── pipeline/ # train, score, monitor pipelines
├── tests/ # unit tests + pipeline smoke tests
├── .github/workflows/ci.yml # GitHub Actions CI
├── requirements.txt
└── README.md

## MLOps Pipeline Steps:

1) Train job

Input: data/raw/*.log

Output:
models/vectorizer.pkl
models/isoforest.pkl
models/metadata.json (training date, data hash, parameters)

Also logs to MLflow:

- params: n_estimators, ngram_range, max_features
- metrics: reconstruction proxy or score distribution stats
- artifacts: the model files + metadata

2) Score job

Input: new logs (file or exported CloudWatch logs)

Output:
outputs/anomalies.csv (topK anomalous logs, line, normalized, score)
outputs/summary.json (count, anomaly_rate, top patterns)

3) Monitor job

Input: outputs/summary.json + previous runs (stored locally or in MLflow)

Track:
anomaly_rate (if it spikes, something changed)

log volume
token/vocabulary drift proxy (e.g., fraction of tokens unseen during training)

## Steps to run MLflow UI locally

### PreRequisites
- Navigate to Project folder. Make sure you see: requirements.txt, src\, scripts\
- create virtual environment: 
```
python -m venv .venv
```
- Activate virtual environment:
```
.\.venv\Scripts\Activate.ps1
```
- Install Packages:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 0 - Generate Kubernetes/EKS Logs (Synthetic Data)

Production logs are often unavailable; therefore, this project uses simulation, as recommended in the course guidelines.
Generate logs:
```
python scripts/generate_logs.py
```
This creates:
- data/raw/events.log
- data/raw/coredns.log
- data/raw/aws-node.log
- data/raw/all.log
- data/raw/dataset_meta.json

### Step 1 — Start MLflow UI pointing to `mlruns/`

From the repository root directory, run:

```
mlflow server \
  --backend-store-uri ./mlruns \
  --default-artifact-root ./mlruns \
  --host 127.0.0.1 \
  --port 5000
```

### Step 2 - In a NEW PowerShell terminal, activate venv

Open a new PowerShell window, go to repo root, and:

```
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Set the Tracking URI to Your Local MLflow Server

Set the `MLFLOW_TRACKING_URI` environment variable so MLflow points to your local server.

#### For Windows PowerShell:
```powershell
$env:MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
```

For Quick verification run:
```
python -c "import mlflow; print(mlflow.get_tracking_uri())"
```

Expected Output:
http://127.0.0.1:5000

### Step 4: ### Step 5 — Run the `ci-k8s-log-anomaly` Experiment Locally

Execute the following commands from the repository root:

1. Train
```
python -m src.pipeline.train \
  --data data/raw/all.log \
  --experiment ci-k8s-log-anomaly
```

2. Score
```
python -m src.pipeline.score \
  --data data/raw/all.log \
  --experiment ci-k8s-log-anomaly \
  --topk 50
```

3. Monitor
```
python -m src.pipeline.monitor \
  --experiment ci-k8s-log-anomaly
```

Then refresh MLflow UI and open the experiment:
- ci-k8s-log-anomaly
- You should see runs: train, score, monitor

## Continuous Integration (GitHub Actions)

The CI pipeline:
- Installs dependencies
- runs unit tests
- executes a full pipeline smoke test (generate → train → score → monitor)

This ensures that changes to the codebase do not break core functionality and that the system remains executable from scratch.





