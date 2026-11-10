from time import perf_counter

from fastapi import Request, Response
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


def instrument_app(app):
    """为FastAPI加指标；也可复用于后续真实RAG接口。单进程教学配置。"""
    registry = CollectorRegistry()
    requests = Counter(
        "agentguide_http_requests_total", "Completed API requests",
        ["method", "route", "status"], registry=registry,
    )
    duration = Histogram(
        "agentguide_http_request_duration_seconds", "Time until response headers",
        ["method", "route"], registry=registry,
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    )

    @app.middleware("http")
    async def record_metrics(request: Request, call_next):
        if request.url.path in {"/metrics", "/health", "/docs", "/openapi.json", "/favicon.ico"}:
            return await call_next(request)
        start = perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            # 用路由模板，避免将每个用户问题/动态URL变成一个标签。
            route = getattr(request.scope.get("route"), "path", "unmatched")
            requests.labels(request.method, route, str(status)).inc()
            duration.labels(request.method, route).observe(perf_counter() - start)

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(content=generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST})

    return registry
