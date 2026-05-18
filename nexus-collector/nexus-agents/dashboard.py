import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx


st.set_page_config(
    page_title="Nexus AI Observability Dashboard",
    page_icon="🧠",
    layout="wide"
)


METRICS_FILE = "pod_metrics.json"
ALERTS_FILE = "alerts.json"
CORRELATIONS_FILE = "correlations.json"
DEPENDENCIES_FILE = "dependencies.json"


def load_json(filename, default_value):
    if not os.path.exists(filename):
        return default_value

    try:
        with open(filename, "r") as file:
            return json.load(file)
    except Exception:
        return default_value


def severity_color(severity):
    severity = str(severity).lower()

    if severity == "critical":
        return "🔴 Critical"
    if severity == "high":
        return "🟠 High"
    if severity == "warning":
        return "🟡 Warning"

    return "🟢 Normal"


def generate_ai_recommendation(alert):
    agent = alert.get("agent", "")
    pod = alert.get("pod", "unknown pod")
    namespace = alert.get("namespace", "default")

    if agent == "CPUAgent":
        return (
            f"Investigate CPU-heavy operations in `{namespace}/{pod}`. "
            f"Check recent traffic spikes, inefficient loops, heavy API calls, "
            f"or missing resource limits."
        )

    if agent == "MemoryAgent":
        return (
            f"Check memory usage in `{namespace}/{pod}`. "
            f"Possible causes include memory leaks, large payloads, bad caching, "
            f"or insufficient memory limits."
        )

    if agent == "RestartAgent":
        return (
            f"Inspect logs for `{namespace}/{pod}` using `kubectl logs`. "
            f"Also check `kubectl describe pod` for OOMKilled, CrashLoopBackOff, "
            f"or failed probes."
        )

    if agent == "StatusAgent":
        return (
            f"`{namespace}/{pod}` is not running. Check image pull errors, "
            f"scheduling issues, failed probes, or insufficient cluster resources."
        )

    return f"Review `{namespace}/{pod}` manually for abnormal behavior."


def create_dependency_graph(dependencies, alerts, correlations):
    graph = nx.DiGraph()

    alert_pods = {alert.get("pod") for alert in alerts}
    correlated_pods = set()

    for correlation in correlations:
        correlated_pods.add(correlation.get("source_pod"))
        correlated_pods.add(correlation.get("related_pod"))

    for source, targets in dependencies.items():
        graph.add_node(source)

        for target in targets:
            graph.add_node(target)
            graph.add_edge(source, target)

    if len(graph.nodes) == 0:
        return None

    pos = nx.spring_layout(graph, seed=42)

    edge_x = []
    edge_y = []

    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1),
        hoverinfo="none",
        mode="lines"
    )

    node_x = []
    node_y = []
    node_text = []
    node_size = []

    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

        if node in correlated_pods:
            node_size.append(35)
        elif node in alert_pods:
            node_size.append(28)
        else:
            node_size.append(20)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hoverinfo="text",
        marker=dict(
            size=node_size,
            line=dict(width=2)
        )
    )

    figure = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Service Dependency Graph",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=20, r=20, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=500
        )
    )

    return figure


def main():
    st.title("🧠 Nexus AI Observability Dashboard")
    st.caption("Real-time pod discovery, anomaly detection, dependency correlation, and AI recommendations")

    metrics = load_json(METRICS_FILE, [])
    alerts = load_json(ALERTS_FILE, [])
    correlations = load_json(CORRELATIONS_FILE, [])
    dependencies = load_json(DEPENDENCIES_FILE, {})

    auto_refresh = st.sidebar.checkbox("Auto refresh", value=True)
    refresh_seconds = st.sidebar.slider("Refresh interval seconds", 2, 20, 5)

    if auto_refresh:
        st.sidebar.info(f"Dashboard refreshes every {refresh_seconds} seconds.")
        st.markdown(
            f"""
            <meta http-equiv="refresh" content="{refresh_seconds}">
            """,
            unsafe_allow_html=True
        )

    st.sidebar.success("Dashboard connected to local JSON pipeline")

    total_pods = len(metrics)
    total_alerts = len(alerts)
    total_correlations = len(correlations)
    affected_pods = len(set([alert.get("pod") for alert in alerts]))

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Pods", total_pods)
    col2.metric("Active Alerts", total_alerts)
    col3.metric("Correlations", total_correlations)
    col4.metric("Affected Pods", affected_pods)

    st.divider()

    # ---------------- Live Pod Table ----------------
    st.subheader("📦 Live Pod Table")

    if metrics:
        metrics_df = pd.DataFrame(metrics)

        display_df = metrics_df.copy()

        if "cpu_millicores" in display_df.columns and "cpu" not in display_df.columns:
            display_df["cpu"] = display_df["cpu_millicores"]

        if "memory_mib" in display_df.columns and "memory" not in display_df.columns:
            display_df["memory"] = display_df["memory_mib"]

        if "restart_count" in display_df.columns and "restarts" not in display_df.columns:
            display_df["restarts"] = display_df["restart_count"]

        useful_columns = [
            col for col in [
                "timestamp",
                "namespace",
                "pod",
                "status",
                "cpu",
                "memory",
                "restarts",
                "node"
            ]
            if col in display_df.columns
        ]

        st.dataframe(
            display_df[useful_columns],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No pod metrics found. Run collector first.")

    st.divider()

    # ---------------- CPU and RAM Graphs ----------------
    st.subheader("📊 CPU and Memory Usage")

    if metrics:
        graph_df = pd.DataFrame(metrics)

        if "cpu_millicores" in graph_df.columns and "cpu" not in graph_df.columns:
            graph_df["cpu"] = graph_df["cpu_millicores"]

        if "memory_mib" in graph_df.columns and "memory" not in graph_df.columns:
            graph_df["memory"] = graph_df["memory_mib"]

        left, right = st.columns(2)

        if "pod" in graph_df.columns and "cpu" in graph_df.columns:
            cpu_chart = px.bar(
                graph_df,
                x="pod",
                y="cpu",
                title="CPU Usage by Pod",
                labels={"cpu": "CPU Usage", "pod": "Pod"}
            )
            left.plotly_chart(cpu_chart, use_container_width=True)

        if "pod" in graph_df.columns and "memory" in graph_df.columns:
            memory_chart = px.bar(
                graph_df,
                x="pod",
                y="memory",
                title="Memory Usage by Pod",
                labels={"memory": "Memory Usage", "pod": "Pod"}
            )
            right.plotly_chart(memory_chart, use_container_width=True)
    else:
        st.info("CPU/RAM graphs will appear after metrics are collected.")

    st.divider()

    # ---------------- Anomaly Timeline ----------------
    st.subheader("🚨 Anomaly Timeline")

    if alerts:
        alerts_df = pd.DataFrame(alerts)

        if "timestamp" in alerts_df.columns:
            alerts_df["timestamp"] = pd.to_datetime(alerts_df["timestamp"], errors="coerce")

        alerts_df["severity_display"] = alerts_df["severity"].apply(severity_color)

        st.dataframe(
            alerts_df[
                [
                    col for col in [
                        "timestamp",
                        "severity_display",
                        "agent",
                        "namespace",
                        "pod",
                        "message"
                    ]
                    if col in alerts_df.columns
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        if "timestamp" in alerts_df.columns and "pod" in alerts_df.columns:
            timeline = px.scatter(
                alerts_df,
                x="timestamp",
                y="pod",
                color="severity",
                symbol="agent",
                hover_data=["message"],
                title="Anomaly Timeline"
            )
            st.plotly_chart(timeline, use_container_width=True)
    else:
        st.success("No anomalies detected.")

    st.divider()

    # ---------------- Correlation Results ----------------
    st.subheader("🔗 Dependency Correlations")

    if correlations:
        for item in correlations:
            st.error(
                f"**{item.get('source_pod')} ↔ {item.get('related_pod')}**  \n\n"
                f"{item.get('message')}"
            )
    else:
        st.info("No dependency impact correlations detected yet.")

    st.divider()

    # ---------------- Dependency Graph ----------------
    st.subheader("🕸️ Dependency Graph")

    graph_figure = create_dependency_graph(dependencies, alerts, correlations)

    if graph_figure:
        st.plotly_chart(graph_figure, use_container_width=True)
    else:
        st.warning("No dependency map found. Add dependencies.json.")

    st.divider()

    # ---------------- AI Recommendations ----------------
    st.subheader("🤖 AI Recommendations")

    if alerts:
        for alert in alerts:
            with st.expander(
                f"{severity_color(alert.get('severity'))} | {alert.get('agent')} | {alert.get('pod')}"
            ):
                st.write(alert.get("message"))
                st.markdown("**Recommended Action:**")
                st.info(generate_ai_recommendation(alert))
    else:
        st.success("No AI recommendations needed. System looks healthy.")

    st.divider()

    # ---------------- Affected Pods ----------------
    st.subheader("🎯 Affected Pods")

    if alerts:
        affected = {}

        for alert in alerts:
            pod = alert.get("pod")
            affected.setdefault(pod, [])
            affected[pod].append(alert.get("agent"))

        affected_rows = []

        for pod, agents in affected.items():
            affected_rows.append(
                {
                    "pod": pod,
                    "triggered_agents": ", ".join(set(agents)),
                    "alert_count": len(agents)
                }
            )

        st.dataframe(
            pd.DataFrame(affected_rows),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("No affected pods found.")


if __name__ == "__main__":
    main()
