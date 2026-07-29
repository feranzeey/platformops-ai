import requests

PROMETHEUS_URL = "http://localhost:9090"


def query(promql):

    try:

        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={
                "query": promql
            },
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        return {
            "status": "error",
            "error": str(e)
        }


def get_metric_value(promql):

    result = query(promql)

    try:

        return float(
            result["data"]["result"][0]["value"][1]
        )

    except Exception:

        return 0.0


def get_metrics():

    cpu_value = get_metric_value("sum(rate(container_cpu_usage_seconds_total[5m]))")

    memory_value = get_metric_value("sum(container_memory_usage_bytes)")

    disk_value = get_metric_value("sum(node_filesystem_avail_bytes)")

    up_value = get_metric_value("up")

    return {

        "cpu": round(cpu_value, 2),
        "memory": round(memory_value, 2),
        "disk": round(disk_value, 2),
        "up": up_value

    }