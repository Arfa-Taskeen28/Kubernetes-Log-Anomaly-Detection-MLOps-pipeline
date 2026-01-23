.PHONY: venv install mlflow train score monitor demo test lint

PY=python
DATA?=data/raw/events.log
MLFLOW_URI?=http://127.0.0.1:5000
EXP?=k8s-log-anomaly

venv:
	$(PY) -m venv .venv

install:
	. .venv/bin/activate && pip install -r requirements.txt

mlflow:
	docker compose up -d mlflow
	@echo "MLflow UI: http://127.0.0.1:5000"

train:
	MLFLOW_TRACKING_URI=$(MLFLOW_URI) $(PY) -m src.pipeline.train --data $(DATA) --experiment $(EXP)

score:
	MLFLOW_TRACKING_URI=$(MLFLOW_URI) $(PY) -m src.pipeline.score --data $(DATA) --experiment $(EXP) --topk 50

monitor:
	MLFLOW_TRACKING_URI=$(MLFLOW_URI) $(PY) -m src.pipeline.monitor --experiment $(EXP)

demo: train score monitor

test:
	$(PY) -m pytest -q

lint:
	@echo "Optional: add ruff/black later (not required for 1-day scope)"
