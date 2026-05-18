# Nexus Demo

An automated Kubernetes monitoring and AI-driven root cause analysis engine powered by Python agents and a Streamlit dashboard.

## Project Directory Structure

```text
nexus-demo/
│
├── demo-services.yaml
├── load-generator.yaml
├── README.md
│
└── nexus-collector/
    │
    ├── collector.py
    ├── main.py
    ├── dashboard.py
    ├── pod_metrics.json
    ├── alerts.json
    ├── correlations.json
    │
    ├── agents/
    │   ├── cpu_agent.py
    │   ├── memory_agent.py
    │   ├── restart_agent.py
    │   ├── status_agent.py
    │   └── correlation_agent.py 
```

---

## Clone and Run Instructions

Follow these steps to clone and run the project on your local machine.

### Prerequisites

Before running this project, make sure you have installed:
* **Git**
* **Python 3**
* **pip**
* **Docker**
* **Minikube**
* **kubectl**

You can verify your installations using:
```bash
git --version
python3 --version
pip3 --version
docker --version
minikube version
kubectl version --client
```

---

### Step 1: Clone the Repository

Open your terminal and run:
```bash
git clone https://github.com/nishantgoyal01/nexus-demo.git
```

Move into the project folder:
```bash
cd nexus-demo
```

Check project files:
```bash
ls
```
*You should see files like: `demo-services.yaml`, `load-generator.yaml`, `nexus-collector`, and `README.md`.*

---

### Step 2: Start Minikube

Make sure your **Docker Desktop/daemon** is running, then start Minikube:
```bash
minikube start
```

Check whether the Kubernetes node is ready:
```bash
kubectl get nodes
```
*Expected output should show the node in a `Ready` state.*

---

### Step 3: Enable Metrics Server

Enable the native Kubernetes Metrics Server addon:
```bash
minikube addons enable metrics-server
```

Verify metrics availability:
```bash
kubectl top pods
```
*Note: If metrics are not visible immediately, wait for 30–60 seconds and run the command again.*

---

### Step 4: Deploy Demo Kubernetes Services

From the root folder (`nexus-demo`), deploy the application ecosystem and load generator:
```bash
kubectl apply -f demo-services.yaml
kubectl apply -f load-generator.yaml
```

Verify the running pods:
```bash
kubectl get pods
```

Verify the running services:
```bash
kubectl get svc
```

---

### Step 5: Move to Collector Folder

Navigate to the collector and agent source directory:
```bash
cd nexus-collector
```

---

### Step 6: Create Python Virtual Environment

Create an isolated virtual environment:
```bash
python3 -m venv venv
```

Activate it based on your operating system:
* **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```
* **Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate
  ```
* **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

---

### Step 7: Install Required Dependencies

Install all the required Python packages for data processing, agent telemetry, and the user interface:
```bash
pip install streamlit pandas plotly networkx kubernetes
```

---

## Running the Project

To run the full system concurrently, **open three separate terminal tabs** and ensure the virtual environment is activated in each.

### Terminal 1: Run Metrics Collector
The collector fetches live Kubernetes pod metrics and writes them to local storage.
```bash
cd nexus-demo/nexus-collector
source venv/bin/activate
python3 collector.py
```
* **Updates file:** `pod_metrics.json`

### Terminal 2: Run AI Agents and Correlation Engine
The AI agents analyze the generated metrics json file to detect anomalies, generate alerts, and pinpoint root causes.
```bash
cd nexus-demo/nexus-collector
source venv/bin/activate
python3 main.py
```
* **Updates files:** `alerts.json`, `correlations.json`

### Terminal 3: Run Streamlit Dashboard
Launch the web interface to visualize topology graphs, metrics, and agent logs.
```bash
cd nexus-demo/nexus-collector
source venv/bin/activate
streamlit run dashboard.py
```
* **Dashboard Access:** Open your browser and navigate to [http://localhost:8501](http://localhost:8501)

---

## Quick Run Commands

If you want to set up and run the stack quickly, use this sequence of commands:

```bash
# Clone and enter repo
git clone https://github.com/nishantgoyal01/nexus-demo.git
cd nexus-demo

# Initialize cluster
minikube start
minikube addons enable metrics-server

# Deploy cluster apps
kubectl apply -f demo-services.yaml
kubectl apply -f load-generator.yaml

# Set up Python env
cd nexus-collector
python3 -m venv venv
source venv/bin/activate
pip install streamlit pandas plotly networkx kubernetes

# Run components (Note: Best run in 3 separate terminals as detailed above)
python3 collector.py & python3 main.py & streamlit run dashboard.py
```
*Note: Running all scripts via a background operator (`&`) in a single terminal combines logs. For optimal debugging, dedicated terminals are highly recommended.*


## Problem Statement

Modern containerized applications run across multiple pods, namespaces, and services. Even in single-node Kubernetes clusters, operators often face challenges such as:

- Sudden CPU spikes
- High memory usage
- Pod restarts
- Unhealthy pod states
- Service dependency issues
- Resource bottlenecks
- Difficulty identifying root causes

Existing tools can show raw metrics, but they often do not clearly answer:

- Which pod is causing the issue?
- Which pods are affected?
- Is there a dependency relationship between failing services?
- What action should the operator take?
- Is the issue CPU, memory, restart, or status related?

NexusOps aims to solve this by combining Kubernetes monitoring with AI-agent-based analysis and a real-time dashboard.

---

## Project Objective

The main objective of NexusOps is to build an AI-powered observability system that can:

- Discover running pods in a Kubernetes cluster
- Collect real-time pod resource metrics
- Detect CPU, memory, restart, and status anomalies
- Correlate issues between pods
- Identify affected workloads
- Generate operational recommendations
- Display insights using a Streamlit dashboard

---

## Key Features

### 1. Real-Time Pod Resource Discovery

NexusOps collects pod-level information such as:

- Pod name
- Namespace
- CPU usage
- Memory usage
- Restart count
- Pod status
- Health condition

---

### 2. Multi-Agent Analysis

The system uses multiple analysis agents, where each agent focuses on one specific resource or behavior.

Implemented agents include:

- CPU Agent
- Memory Agent
- Restart Agent
- Status Agent
- Correlation Agent

Each agent analyzes pod metrics and generates alerts based on predefined thresholds and rules.

---

### 3. Anomaly Detection

NexusOps detects common Kubernetes issues such as:

- CPU spikes
- High memory usage
- Pod restart loops
- Pending pods
- Failed pods
- Unstable workloads

Example alert:

```text
[CRITICAL] CPUAgent | default/payment-service | CPU spike detected in payment-service. CPU usage is 91%.
