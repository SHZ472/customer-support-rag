"""Replay the sample questions and check Prometheus through Grafana."""

import json
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8150"
GRAFANA = "http://127.0.0.1:3150"
OPENER = build_opener(ProxyHandler({}))


def request_json(url, payload=None):
    request = Request(url)
    if payload is not None:
        request.data = json.dumps(payload).encode("utf-8")
        request.add_header("Content-Type", "application/json")
    try:
        response = OPENER.open(request, timeout=10)
    except HTTPError as exc:
        response = exc
    with response:
        return response.code, json.load(response)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    status, spec = request_json(f"{API}/openapi.json")
    require(status == 200 and "post" in spec["paths"].get("/ask", {}), "POST /ask is absent.")
    fixtures = json.loads((ROOT / "data" / "acceptance_cases.json").read_text(encoding="utf-8"))
    for case in fixtures["cases"]:
        status, result = request_json(f"{API}/ask", {"question": case["question"]})
        expected_sources = [case["source"]] if case["source"] is not None else []
        require(status == 200 and result["route"] == case["route"] and result["sources"] == expected_sources
                and all(fact in result["answer"] for fact in case["must_include"]),
                f"Failed case {case['id']}: HTTP {status}, {result}")
        print(f"PASS {case['id']} ({result['route']})")

    status, _ = request_json(f"{API}/ask", {"question": "   "})
    require(status == 422, "Blank input should return HTTP 422.")
    print("PASS blank_question (HTTP 422)")

    query = urlencode({"query": 'up{job="agentguide-customer-rag"}'})
    url = f"{GRAFANA}/api/datasources/proxy/uid/day49-customer-prometheus/api/v1/query?{query}"
    deadline = monotonic() + 20
    while monotonic() < deadline:
        status, result = request_json(url)
        if status == 200 and any(float(row["value"][1]) == 1 for row in result["data"]["result"]):
            break
        sleep(1)
    else:
        raise RuntimeError("Grafana could not read a healthy Prometheus target.")

    status, dashboard = request_json(f"{GRAFANA}/api/dashboards/uid/agentguide-customer-rag")
    require(status == 200 and len(dashboard["dashboard"]["panels"]) == 4, "Grafana dashboard is missing.")
    print("PASS Grafana dashboard and Prometheus scrape")


if __name__ == "__main__":
    main()
