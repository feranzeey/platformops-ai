import requests

PROMETHEUS_URL = "http://localhost:9090"


def query(promql):
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "success":
            return None

        return data

    except requests.RequestException as e:
        print(f"Prometheus request error: {e}")
        return None

    except Exception as e:
        print(f"Prometheus error: {e}")
        return None


def get_metric_value(promql):
    result = query(promql)

    try:
        return float(
            result["data"]["result"][0]["value"][1]
        )
    except (TypeError, KeyError, IndexError, ValueError):
        return 0.0


def get_metrics():

    # =====================================
    # CPU Usage %
    # =====================================

    cpu_value = get_metric_value(
        '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
    )

    # =====================================
    # Memory Usage %
    # =====================================

    memory_value = get_metric_value(
        '100 * (1 - '
        '(sum(node_memory_MemAvailable_bytes) / '
        'sum(node_memory_MemTotal_bytes)))'
    )

    # =====================================
    # Disk Usage %
    # =====================================

    disk_value = get_metric_value(
        '100 * (1 - '
        '(sum(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}) / '
        'sum(node_filesystem_size_bytes{fstype!~"tmpfs|overlay"})))'
    )

    # =====================================
    # Prometheus / Targets Up
    # =====================================

    up_value = get_metric_value(
        'avg(up) * 100'
    )

    return {
        "cpu": round(cpu_value, 2),
        "memory": round(memory_value, 2),
        "disk": round(disk_value, 2),
        "up": round(up_value, 2)
    }