import os
import yaml
from datetime import datetime, timezone

from flask import Flask, render_template, request

from k8s_service import (
    get_pods,
    get_deployments,
    get_services,
    get_nodes,
    get_namespaces
)

from events import get_events
from timeline import (
    build_incident_timeline,
    summarize_timeline,
    generate_incident_story
)
from prometheus import get_metrics
from github_service import get_latest_commit
from ai import analyze_cluster
from ai.investigation import investigate_deployment
from ai.report_generator import generate_incident_report
from health import calculate_health
from severity import calculate_severity
from repair import restart_deployment

app = Flask(__name__)

INCIDENTS_DIR = "incidents"


def save_incident(pod_name, problem, root_cause, action, status="resolved"):

    os.makedirs(INCIDENTS_DIR, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(INCIDENTS_DIR, f"{today}.yaml")

    entry = {
        "incident": {
            "pod": pod_name
        },
        "problem": problem,
        "rootcause": root_cause,
        "action": action,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    existing = []

    if os.path.exists(filepath):

        with open(filepath, "r") as f:

            loaded = yaml.safe_load(f)

            if isinstance(loaded, list):
                existing = loaded

            elif loaded:
                existing = [loaded]

    existing.append(entry)

    with open(filepath, "w") as f:
        yaml.dump(existing, f, sort_keys=False)


def load_incident_timeline(limit=10):

    if not os.path.isdir(INCIDENTS_DIR):
        return []

    timeline = []

    for filename in sorted(os.listdir(INCIDENTS_DIR), reverse=True):

        if not filename.endswith(".yaml"):
            continue

        filepath = os.path.join(INCIDENTS_DIR, filename)

        with open(filepath, "r") as f:
            loaded = yaml.safe_load(f) or []

        if isinstance(loaded, dict):
            loaded = [loaded]

        for item in loaded:
            item["date"] = filename.replace(".yaml", "")
            timeline.append(item)

    timeline.sort(
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )

    return timeline[:limit]


@app.route("/", methods=["GET", "POST"])
def home():

    report = None

    if request.method == "POST":

        # =====================================
        # Kubernetes Resources
        # =====================================

        pods = get_pods()
        deployments = get_deployments()
        services = get_services()
        nodes = get_nodes()
        namespaces = get_namespaces()

        events = get_events()

        # =====================================
        # AI Incident Timeline
        # =====================================

        incident_timeline = build_incident_timeline(events)

        timeline_summary = summarize_timeline(
            incident_timeline
        )

        incident_story = generate_incident_story(
            incident_timeline
        )

        # =====================================
        # AI Deployment Investigation
        # =====================================

        investigations = []
        incident_reports = []

        for deployment in deployments:

            result = investigate_deployment(deployment)

            if result:

                investigations.append(result)

                incident_reports.append(
                    generate_incident_report(result)
                )

        # =====================================
        # Prometheus Metrics
        # =====================================

        metrics = get_metrics()

        # =====================================
        # GitHub Activity
        # =====================================

        github = get_latest_commit()

        # =====================================
        # Cluster Health
        # =====================================

        health = calculate_health(
            pods,
            deployments,
            nodes,
            events,
            metrics
        )

        # =====================================
        # Incident Severity
        # =====================================

        severity = calculate_severity(
            logs=pods["logs"],
            events=events,
            metrics=metrics
        )

        # =====================================
        # AI Cluster Analysis
        # =====================================

        analysis = analyze_cluster(
            logs=pods["logs"],
            events=events,
            metrics=metrics,
            github=github
        )

        analysis["severity"] = severity

        # =====================================
        # Save Incident History
        # =====================================

        if severity != "LOW":

            save_incident(
                pod_name=analysis.get(
                    "affected_pod",
                    "unknown"
                ),
                problem=analysis.get(
                    "root_cause",
                    "Unclassified issue"
                ),
                root_cause=analysis.get(
                    "root_cause",
                    "Unknown"
                ),
                action="Analyzed by PlatformOps AI",
                status="open"
            )

        # =====================================
        # Dashboard Report
        # =====================================

        report = {

            "pods": pods,
            "deployments": deployments,
            "services": services,
            "nodes": nodes,
            "namespaces": namespaces,
            "events": events,
            "metrics": metrics,
            "github": github,
            "health": health,
            "analysis": analysis,
            "severity": severity,

            # Historical Incident History

            "history": load_incident_timeline(),

            # Live Kubernetes Timeline

            "timeline": incident_timeline,

            # AI Timeline Summary

            "timeline_summary": timeline_summary,

            # AI Incident Story

            "timeline_story": incident_story,

            # AI Investigation

            "investigations": investigations,

            # Professional Incident Reports

            "incident_reports": incident_reports
        }

    return render_template(
        "index.html",
        report=report
    )

   # =====================================
# Repair Deployment
# =====================================

@app.route("/repair/<deployment>")
def repair(deployment):
    result = restart_deployment(deployment)

    save_incident(
        pod_name=deployment,
        problem="AI Auto Repair",
        root_cause="PlatformOps AI Automatic Repair",
        action=result["message"],
        status="resolved" if result["success"] else "failed"
    )

    return render_template(
        "repair.html",
        result=result
    )

# =====================================
# Incident History
# =====================================

@app.route("/history")
def history():

    history = load_incident_timeline()

    return render_template(
        "history.html",
        history=history
    )


# =====================================
# Run Application
# =====================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )