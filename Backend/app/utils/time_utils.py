from datetime import datetime

def parse_timestamp(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
