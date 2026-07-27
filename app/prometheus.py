import requests


PROMETHEUS_URL = "http://localhost:9090"


def query(query):

    try:

        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={
                "query": query
            },
            timeout=5
        )

        return response.json()

    except Exception as e:

        return {
            "error": str(e)
        }


def get_metrics():

    cpu = query("up")

    return {
        "cpu": cpu
    }