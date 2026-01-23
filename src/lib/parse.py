import re

IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}\b")
HEX_RE = re.compile(r"\b[0-9a-fA-F]{10,}\b")
NUM_RE = re.compile(r"\b\d+\b")

def normalize(line: str) -> str:
    s = line.strip()
    if not s:
        return s

    s = IP_RE.sub("<IP>", s)
    s = UUID_RE.sub("<UUID>", s)
    s = HEX_RE.sub("<HEX>", s)
    s = NUM_RE.sub("<NUM>", s)

    # Reduce k8s identifier noise
    s = re.sub(r"\bpod/[a-z0-9-]+\b", "pod/<POD>", s)
    s = re.sub(r"\bdeployment/[a-z0-9-]+\b", "deployment/<DEP>", s)
    s = re.sub(r"\breplicaset/[a-z0-9-]+\b", "replicaset/<RS>", s)
    s = re.sub(r"\bnode/[a-z0-9.-]+\b", "node/<NODE>", s)

    return s
