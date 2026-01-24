from __future__ import annotations
import random
from datetime import datetime, timedelta
from pathlib import Path
import json
import uuid

random.seed(42)

NAMESPACES = ["default", "kube-system", "observability", "payments", "auth", "ingress-nginx"]
NODES = [f"ip-10-0-{i}-{j}.ec2.internal" for i in range(1, 6) for j in range(10, 60, 10)]
PODS = {
    "default": ["web", "api", "worker", "frontend"],
    "kube-system": ["coredns", "aws-node", "kube-proxy", "metrics-server"],
    "observability": ["prometheus", "grafana", "loki"],
    "payments": ["pay-api", "pay-worker"],
    "auth": ["auth-api", "oauth"],
    "ingress-nginx": ["ingress-nginx-controller"]
}

# Normal (high-frequency) patterns
NORMAL_TEMPLATES = [
    "Normal Scheduled Successfully assigned {ns}/{pod}-{suffix} to {node}",
    "Normal Pulled Container image \"{image}\" already present on machine",
    "Normal Created Created container {container}",
    "Normal Started Started container {container}",
    "Normal SuccessfulCreate Created pod: {pod}-{suffix}",
    "Normal ScalingReplicaSet Scaled up replica set {pod}-{rs} to {n} from {m}",
    "Normal LeaderElection {pod}-{suffix} became leader",
    "Normal Synced Successfully synced {pod}-{suffix}",
    "Normal AddedInterface Add eth0 [{ip}] from eni {eni}",
]

# Anomalous (lower frequency) patterns
ANOM_TEMPLATES = [
    "Warning BackOff Back-off restarting failed container {container} in pod {ns}/{pod}-{suffix}",
    "Warning CrashLoopBackOff pod/{pod}-{suffix} CrashLoopBackOff",
    "Warning OOMKilled Container {container} in pod {ns}/{pod}-{suffix} was killed due to OOM",
    "Warning FailedScheduling 0/{total} nodes are available: {reason}",
    "Warning ImagePullBackOff Back-off pulling image \"{image}\"",
    "Warning ErrImagePull Failed to pull image \"{image}\": rpc error: code = Unknown desc = Error response from daemon: pull access denied",
    "Warning Unhealthy Readiness probe failed: Get \"http://{ip}:{port}/health\": dial tcp {ip}:{port}: i/o timeout",
    "Warning FailedMount Unable to attach or mount volumes: timed out waiting for the condition",
    "Warning NodeNotReady Node {node} status is now: NodeNotReady",
    "Warning DiskPressure Node {node} status is now: NodeHasDiskPressure",
    "Warning MemPressure Node {node} status is now: NodeHasMemoryPressure",
    "Warning FailedCreate Error creating: pods \"{pod}-{suffix}\" is forbidden: error looking up service account {ns}/default: serviceaccount \"default\" not found",
    "Warning TLSHandshakeTimeout net/http: TLS handshake timeout",
    "Warning DNSConfigForming Nameserver limits were exceeded, some nameservers have been omitted, the applied nameserver line is: {dns_line}",
]

IMAGES = [
    "nginx:1.25",
    "python:3.11-slim",
    "public.ecr.aws/eks/aws-node:v1.14.1",
    "registry.k8s.io/coredns/coredns:v1.11.1",
    "busybox:1.36",
    "ghcr.io/company/pay-api:2.3.1",
    "ghcr.io/company/auth-api:1.9.0",
]

def rand_ip():
    return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def rand_eni():
    return "eni-" + uuid.uuid4().hex[:12]

def rand_suffix():
    return uuid.uuid4().hex[:6]

def rand_rs():
    return uuid.uuid4().hex[:8]

def choose_pod(ns: str):
    base = random.choice(PODS[ns])
    return base

def event_line(ts: datetime, msg: str) -> str:
    # Looks similar to `kubectl get events -A --sort-by=.lastTimestamp`
    # TIME  TYPE    REASON      OBJECT                     MESSAGE
    # We'll embed timestamp at start for consistency.
    return f"{ts.isoformat()}Z {msg}"

def generate_events(n_lines=5000, anomaly_ratio=0.08):
    now = datetime.utcnow()
    start = now - timedelta(hours=6)

    lines = []
    for i in range(n_lines):
        ts = start + timedelta(seconds=int(i * (6*3600 / max(n_lines,1))))
        ns = random.choice(NAMESPACES)
        pod = choose_pod(ns)
        node = random.choice(NODES)
        container = random.choice(["app", "sidecar", "agent", "proxy"])
        image = random.choice(IMAGES)
        ip = rand_ip()
        eni = rand_eni()
        suffix = rand_suffix()
        rs = rand_rs()
        port = random.choice([80, 443, 8080, 9090])

        is_anom = random.random() < anomaly_ratio
        if is_anom:
            tmpl = random.choice(ANOM_TEMPLATES)
            reason = random.choice([
                "Insufficient cpu", "Insufficient memory", "node(s) had taint {node.kubernetes.io/not-ready: }",
                "0/5 nodes available: pod has unbound immediate PersistentVolumeClaims",
                "preemption: 0/5 nodes are available: No preemption victims found for incoming pod"
            ])
            dns_line = " ".join([rand_ip() for _ in range(5)])
            msg = tmpl.format(
                ns=ns, pod=pod, node=node, container=container, image=image, ip=ip, eni=eni,
                suffix=suffix, rs=rs, n=random.randint(2,6), m=random.randint(0,2),
                total=random.randint(3,8), reason=reason, port=port, dns_line=dns_line
            )
        else:
            tmpl = random.choice(NORMAL_TEMPLATES)
            msg = tmpl.format(
                ns=ns, pod=pod, node=node, container=container, image=image, ip=ip, eni=eni,
                suffix=suffix, rs=rs, n=random.randint(2,6), m=random.randint(0,2)
            )

        lines.append(event_line(ts, msg))

    return lines

def generate_component_logs(n_lines=2500, component="coredns", anomaly_ratio=0.06):
    now = datetime.utcnow()
    start = now - timedelta(hours=6)
    lines = []

    normal = [
        f'{component}[{random.randint(100,999)}]: INFO: plugin/ready: Still waiting on: "kubernetes"',
        f'{component}[{random.randint(100,999)}]: INFO: plugin/kubernetes: {random.randint(10,100)} resource records',
        f'{component}[{random.randint(100,999)}]: INFO: Reloading configuration',
        f'{component}[{random.randint(100,999)}]: INFO: Health check OK',
    ]
    anomalous = [
        f'{component}[{random.randint(100,999)}]: ERROR: plugin/errors: {rand_ip()}:{random.randint(10000,60000)} - {random.choice(["i/o timeout", "no such host", "SERVFAIL", "NXDOMAIN"])}',
        f'{component}[{random.randint(100,999)}]: ERROR: upstream {rand_ip()}:53: read udp {rand_ip()}:{random.randint(10000,60000)}->{rand_ip()}:53: i/o timeout',
        f'{component}[{random.randint(100,999)}]: WARN: too many open files',
        f'{component}[{random.randint(100,999)}]: ERROR: failed to list *v1.Service: Get "https://{rand_ip()}:443": net/http: TLS handshake timeout',
    ]

    for i in range(n_lines):
        ts = start + timedelta(seconds=int(i * (6*3600 / max(n_lines,1))))
        is_anom = random.random() < anomaly_ratio
        msg = random.choice(anomalous if is_anom else normal)
        lines.append(f"{ts.isoformat()}Z {msg}")
    return lines

def write_outputs(base_dir="data/raw", n_events=6000):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)

    events = generate_events(n_lines=n_events, anomaly_ratio=0.08)
    coredns = generate_component_logs(n_lines=2500, component="coredns", anomaly_ratio=0.06)
    awsnode = generate_component_logs(n_lines=2500, component="aws-node", anomaly_ratio=0.05)

    (base / "events.log").write_text("\n".join(events) + "\n", encoding="utf-8")
    (base / "coredns.log").write_text("\n".join(coredns) + "\n", encoding="utf-8")
    (base / "aws-node.log").write_text("\n".join(awsnode) + "\n", encoding="utf-8")

    # Combined file for convenience
    all_lines = events + coredns + awsnode
    (base / "all.log").write_text("\n".join(all_lines) + "\n", encoding="utf-8")

    meta = {
        "n_events": len(events),
        "n_coredns": len(coredns),
        "n_aws_node": len(awsnode),
        "total": len(all_lines),
        "anomaly_ratio_events": 0.08,
        "anomaly_ratio_coredns": 0.06,
        "anomaly_ratio_aws_node": 0.05,
        "generated_utc": datetime.utcnow().isoformat() + "Z",
    }
    (base / "dataset_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("Generated:")
    print(f"  {base/'events.log'}")
    print(f"  {base/'coredns.log'}")
    print(f"  {base/'aws-node.log'}")
    print(f"  {base/'all.log'}")
    print(f"  {base/'dataset_meta.json'}")

if __name__ == "__main__":
    write_outputs()
