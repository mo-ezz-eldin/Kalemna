from prometheus_client import Histogram, Gauge


NODE_EXECUTION_TIME = Histogram(
    "langgraph_node_duration_seconds",
    "Time spent executing a specific LangGraph node",
    ["node_name"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0)
)


WAITING_REQUESTS = Gauge(
    "app_waiting_requests_total",
    "Number of requests waiting for a processing slot"
)