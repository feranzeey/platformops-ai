#  PlatformOps AI

> An AI-powered Kubernetes Operations Dashboard that monitors cluster health, detects infrastructure issues, performs root cause analysis, visualizes incidents, generates reports, and automates recovery actions.

---

##  Overview

PlatformOps AI is a DevOps observability and incident management platform built to simplify Kubernetes cluster monitoring and troubleshooting.

Instead of manually checking Kubernetes resources, logs, metrics, and events, PlatformOps AI collects infrastructure data, analyzes it using AI, identifies potential problems, suggests root causes, and provides actionable recommendations from a single dashboard.

The project demonstrates modern DevOps practices including:

- Kubernetes Monitoring
- AI-Assisted Incident Analysis
- Infrastructure Health Checks
- Root Cause Analysis
- Automated Repair Actions
- GitHub Integration
- Prometheus Metrics
- Incident Timeline Visualization
- PDF Report Generation

---

#  Features

###  Kubernetes Cluster Monitoring

- Monitor Pods
- Monitor Deployments
- Monitor Services
- Monitor Nodes
- Monitor Namespaces
- Display Cluster Status

---

###  Infrastructure Health Dashboard

View:

- CPU Usage
- Memory Usage
- Network Usage
- Pod Status
- Restart Counts
- Cluster Health Score

---

###  AI Incident Investigation

Automatically analyzes cluster information to identify:

- Failed Pods
- CrashLoopBackOff
- Image Pull Errors
- High Resource Usage
- Deployment Problems
- Service Availability Issues

Generates human-readable explanations of infrastructure problems.

---

###  Root Cause Analysis

Each investigation includes:

- Problem Summary
- Root Cause
- Severity Level
- Impact Assessment
- Recommended Resolution

---

###  Incident Timeline

Visual timeline of Kubernetes events:

```
Pod Scheduled

↓

Container Started

↓

Readiness Probe Failed

↓

CrashLoopBackOff

↓

Auto Investigation

↓

Deployment Restarted
```

---

###  Historical Incident Tracking

View previous incidents grouped by:

- Today
- Yesterday
- Last Week

Each incident contains:

- Root Cause
- Timeline
- Resolution
- Commands Used
- Duration
- Lessons Learned

---

###  Automated Repair

Supports automated remediation such as:

- Restart Deployment
- Restart Pods
- Recovery Recommendations
- Kubernetes Repair Commands

---

###  PDF Report Generation

Generate downloadable reports including:

- Cluster Summary
- AI Investigation
- Root Cause Analysis
- Health Metrics
- Incident Timeline
- Recommendations

---

###  Resource Charts

Visual charts for:

- CPU Usage
- Memory Usage
- Network Usage
- Restart Trends

---

###  GitHub Integration

Retrieve repository information including:

- Latest Commit
- Commit Author
- Commit Date

Useful for correlating deployments with infrastructure incidents.

---

###  Prometheus Integration

Collects live infrastructure metrics from Prometheus including:

- CPU Usage
- Memory Usage
- Network Metrics
- Cluster Utilization

---

#  Architecture

```
                     Kubernetes Cluster
                             │
                             ▼
                  Kubernetes Python Client
                             │
      ┌──────────────────────┼──────────────────────┐
      │                      │                      │
      ▼                      ▼                      ▼
 Prometheus API        GitHub API          Kubernetes Events
      │                      │                      │
      └──────────────┬───────┴──────────────┬───────┘
                     ▼
              PlatformOps AI Engine
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
 AI Analysis   Incident Timeline  Health Engine
      │              │              │
      └──────────────┼──────────────┘
                     ▼
              Flask Web Dashboard
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 Dashboard      PDF Reports     Auto Repair
```

---

# 🛠 Tech Stack

## Backend

- Python 3.12
- Flask

## Kubernetes

- Kubernetes Python Client
- kubectl
- Minikube

## Monitoring

- Prometheus

## AI

- OpenAI API (optional)
- Custom AI Analysis Engine

## Frontend

- HTML
- CSS
- JavaScript
- Jinja2 Templates

## Reports

- ReportLab
- YAML

## Version Control

- Git
- GitHub

---

#  Project Structure

```
platformops-ai/

│
├── app/
│   ├── main.py
│   ├── ai.py
│   ├── events.py
│   ├── github_service.py
│   ├── health.py
│   ├── k8s_service.py
│   ├── prometheus.py
│   ├── repair.py
│   ├── severity.py
│   ├── timeline.py
│   ├── templates/
│   └── static/
│
├── incidents/
│
├── reports/
│
├── screenshots/
│
├── Dockerfile
├── requirements.txt
├── README.md
└── docker-compose.yml
```

---

#  Installation

## Clone Repository

```bash
git clone https://github.com/feranzeey/platformops-ai.git

cd platformops-ai
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Linux

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Application

```bash
cd app

python main.py
```

Application runs on:

```
http://localhost:5000
```

---

#  Docker

Build

```bash
docker build -t platformops-ai .
```

Run

```bash
docker run -p 5000:5000 platformops-ai
```

---

#  Kubernetes Deployment

Apply Kubernetes manifests

```bash
kubectl apply -f k8s/
```

Verify

```bash
kubectl get pods

kubectl get svc
```

---

#  Screenshots

Include screenshots of:

```
Dashboard

Cluster Analysis

Incident Timeline

Root Cause Analysis

Historical Incidents

PDF Report

Auto Repair

Resource Charts
```

Example folder

```
screenshots/

dashboard.png

timeline.png

analysis.png

report.png

history.png

repair.png
```

---

#  Demo

Recommended demonstration:

- Open Dashboard
- Analyze Cluster
- AI Investigation
- Incident Timeline
- Root Cause Analysis
- Auto Repair
- Generate PDF Report

Duration:

2–3 minutes

---

#  Future Improvements

- User Authentication
- Multi-Cluster Support
- Grafana Integration
- Slack Notifications
- Microsoft Teams Alerts
- Email Notifications
- Predictive Failure Detection
- AI Chat Assistant
- Real-Time WebSockets
- Helm Deployment
- GitHub Actions CI/CD
- Role-Based Access Control (RBAC)

---

#  Learning Outcomes

This project demonstrates knowledge of:

- Kubernetes
- Docker
- Flask
- Python
- DevOps Automation
- Infrastructure Monitoring
- Observability
- Incident Management
- Prometheus
- GitHub API
- YAML
- REST APIs
- AI-assisted Operations

---

#  Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a Pull Request.

---

#  License

This project is licensed under the MIT License.

---

#  Author

**Feranmi**

DevOps Engineer | Cloud Enthusiast | Kubernetes | Docker | Python | CI/CD | Infrastructure Automation

GitHub: https://github.com/feranzeey

LinkedIn: https://www.linkedin.com/in/your-linkedin-profile

---

##  Support

If you found this project helpful, consider giving it a **Star** on GitHub. It helps others discover the project and supports continued development.