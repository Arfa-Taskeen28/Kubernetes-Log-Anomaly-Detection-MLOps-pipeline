from src.lib.parse import normalize

def test_normalize_replaces_ip_and_numbers():
    s = "Error contacting 10.20.30.40 on port 443 after 3 retries"
    out = normalize(s)
    assert "<IP>" in out
    assert "<NUM>" in out