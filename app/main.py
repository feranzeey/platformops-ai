import os
import yaml
from datetime import datetime, timezone, timedelta

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


# =====================================================
# PROJECT PATHS
# =====================================================

# main.py is inside:
# platformops-ai/app/main.py
#
# BASE_DIR becomes:
# platformops-ai/

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

INCIDENTS_DIR = os.path.join(
    BASE_DIR,
    "incidents"
)


# =====================================================
# INCIDENT STORAGE
# =====================================================

def save_incident(
    pod_name,
    problem,
    root_cause,
    action,
    status="resolved"
):

    os.makedirs(
        INCIDENTS_DIR,
        exist_ok=True
    )

    now = datetime.now(timezone.utc)

    today = now.strftime(
        "%Y-%m-%d"
    )

    filepath = os.path.join(
        INCIDENTS_DIR,
        f"{today}.yaml"
    )

    entry = {
        "incident": {
            "pod": pod_name
        },

        "problem": problem,

        "rootcause": root_cause,

        "action": action,

        "status": status,

        "severity": "HIGH",

        "timestamp": now.isoformat()
    }

    existing = []

    if os.path.exists(filepath):

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as f:

                loaded = yaml.safe_load(f)

                if isinstance(
                    loaded,
                    list
                ):

                    existing = loaded

                elif loaded:

                    existing = [loaded]

        except (
            yaml.YAMLError,
            OSError
        ):

            existing = []

    existing.append(entry)

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        yaml.dump(
            existing,
            f,
            sort_keys=False
        )


# =====================================================
# LOAD INCIDENT HISTORY
# =====================================================

def load_incident_timeline(limit=50):

    if not os.path.isdir(
        INCIDENTS_DIR
    ):

        return []

    timeline = []

    for filename in sorted(
        os.listdir(INCIDENTS_DIR),
        reverse=True
    ):

        if not filename.endswith(
            ".yaml"
        ):

            continue

        filepath = os.path.join(
            INCIDENTS_DIR,
            filename
        )

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as f:

                loaded = yaml.safe_load(
                    f
                ) or []

        except (
            yaml.YAMLError,
            OSError
        ):

            continue

        if isinstance(
            loaded,
            dict
        ):

            loaded = [loaded]

        for item in loaded:

            if not isinstance(
                item,
                dict
            ):

                continue

            item["date"] = filename.replace(
                ".yaml",
                ""
            )

            # -------------------------------------------------
            # Extract pod name
            # -------------------------------------------------

            incident_data = item.get(
                "incident",
                {}
            )

            if isinstance(
                incident_data,
                dict
            ):

                item["name"] = incident_data.get(
                    "pod",
                    "Kubernetes Incident"
                )

            else:

                item["name"] = "Kubernetes Incident"


            # -------------------------------------------------
            # Normalize field names
            # -------------------------------------------------

            item["root_cause"] = item.get(
                "rootcause",
                item.get(
                    "root_cause",
                    "Root cause not recorded"
                )
            )

            item["resolution"] = item.get(
                "action",
                "Resolution not recorded"
            )

            item["problem"] = item.get(
                "problem",
                "Incident detected"
            )

            item["status"] = item.get(
                "status",
                "resolved"
            )

            item["severity"] = str(
                item.get(
                    "severity",
                    "MEDIUM"
                )
            ).upper()


            # -------------------------------------------------
            # Date grouping
            # -------------------------------------------------

            item["date_group"] = get_date_group(
                item
            )

            timeline.append(item)


    # Sort newest first

    timeline.sort(
        key=lambda x: x.get(
            "timestamp",
            ""
        ),
        reverse=True
    )

    return timeline[:limit]


# =====================================================
# DATE GROUPING
# =====================================================

def get_date_group(incident):

    timestamp = incident.get(
        "timestamp"
    )

    if timestamp:

        try:

            incident_date = datetime.fromisoformat(
                timestamp.replace(
                    "Z",
                    "+00:00"
                )
            ).date()

        except ValueError:

            incident_date = None

    else:

        incident_date = None


    # Fall back to filename date

    if incident_date is None:

        date_value = incident.get(
            "date"
        )

        try:

            incident_date = datetime.strptime(
                date_value,
                "%Y-%m-%d"
            ).date()

        except (
            ValueError,
            TypeError
        ):

            return "Last Week"


    today = datetime.now(
        timezone.utc
    ).date()

    yesterday = today - timedelta(
        days=1
    )

    week_ago = today - timedelta(
        days=7
    )


    if incident_date == today:

        return "Today"

    if incident_date == yesterday:

        return "Yesterday"

    if incident_date >= week_ago:

        return "Last Week"

    return "Older"


# =====================================================
# MAIN DASHBOARD
# =====================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def home():

    # =================================================
    # KUBERNETES RESOURCES
    # =================================================

    pods = get_pods()

    deployments = get_deployments()

    services = get_services()

    nodes = get_nodes()

    namespaces = get_namespaces()

    events = get_events()


    # =================================================
    # AI INCIDENT TIMELINE
    # =================================================

    incident_timeline = build_incident_timeline(
        events
    )

    timeline_summary = summarize_timeline(
        incident_timeline
    )

    incident_story = generate_incident_story(
        incident_timeline
    )


    # =================================================
    # AI DEPLOYMENT INVESTIGATION
    # =================================================

    investigations = []

    incident_reports = []

    for deployment in deployments:

        result = investigate_deployment(
            deployment
        )

        if result:

            # -------------------------------------------------
            # Preserve the real Kubernetes namespace
            # and deployment name for Auto Repair.
            # ------------------------------------------------- 

            result.setdefault(
                "namespace",
                 deployment.get(
                    "namespace",
                    "default"
                 )
            )
            
            result.setdefault(
                "deployment",
                deployment.get(
                    "name"
                )
            )

            investigations.append(
                result
            )

            incident_reports.append(
                generate_incident_report(
                    result
                )
            )


    # =================================================
    # PROMETHEUS METRICS
    # =================================================

    metrics = get_metrics()


    # =================================================
    # GITHUB ACTIVITY
    # =================================================

    github = get_latest_commit()


    # =================================================
    # CLUSTER HEALTH
    # =================================================

    health = calculate_health(
        pods,
        deployments,
        nodes,
        events,
        metrics
    )


    # =================================================
    # BASE INCIDENT SEVERITY
    # =================================================

    severity = calculate_severity(
        logs=pods.get(
            "logs",
            ""
        ),
        events=events,
        metrics=metrics
    )


    # =================================================
    # ALIGN GLOBAL SEVERITY WITH AI INVESTIGATIONS
    # =================================================

    severity_priority = {
        "LOW": 0,
        "MEDIUM": 1,
        "HIGH": 2,
        "CRITICAL": 3
    }

    for investigation in investigations:

        investigation_severity = str(
            investigation.get(
                "severity",
                "LOW"
            )
        ).upper()

        if (
            investigation_severity
            in severity_priority
        ):

            if (
                severity_priority[
                    investigation_severity
                ]
                >
                severity_priority.get(
                    severity,
                    0
                )
            ):

                severity = investigation_severity


    # =================================================
    # AI CLUSTER ANALYSIS
    # =================================================

    analysis = analyze_cluster(
        logs=pods.get(
            "logs",
            ""
        ),
        events=events,
        metrics=metrics,
        github=github
    )

    analysis["severity"] = severity


    # =================================================
    # SAVE INCIDENT HISTORY
    # =================================================

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


    # =================================================
    # LOAD HISTORICAL INCIDENTS
    # =================================================

    history = load_incident_timeline()


    # =================================================
    # DASHBOARD REPORT
    # =================================================

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

        # Historical incidents
        "history": history,

        # Live Kubernetes timeline
        "timeline": incident_timeline,

        # AI timeline summary
        "timeline_summary": timeline_summary,

        # AI incident story
        "timeline_story": incident_story,

        # AI investigations
        "investigations": investigations,

        # Generated incident reports
        "incident_reports": incident_reports

    }


    return render_template(
        "index.html",
        report=report
    )


# =====================================================
# AUTO REPAIR DEPLOYMENT
# =====================================================

@app.route(
    "/repair/<namespace>/<deployment>"
)
def repair(namespace, deployment):

    result = restart_deployment(
        deployment,
        namespace
    )

    save_incident(
        pod_name=deployment,
        problem="AI Auto Repair",
        root_cause="PlatformOps AI Automatic Repair",
        action=result.get(
            "message",
            "Deployment repair completed"
        ),
        status=(
            "resolved"
            if result.get("success")
            else "failed"
        )
    )

    return render_template(
        "repair.html",
        result=result,
        deployment=deployment
    )


# =====================================================
# INCIDENT HISTORY
# =====================================================

@app.route(
    "/history"
)
def history():

    incidents = load_incident_timeline(
        limit=50
    )

    return render_template(
        "history.html",
        incidents=incidents
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )