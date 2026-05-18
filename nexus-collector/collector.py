from kubernetes import client, config
from datetime import datetime
import time
import json


def load_kubernetes_config():
    """
    Loads Kubernetes config from your local machine.

    This allows Python to connect to the same cluster
    that kubectl is connected to.
    """
    config.load_kube_config()


def get_pod_restart_count(pod):
    """
    Calculates total restart count for all containers inside a pod.
    One pod can have multiple containers.
    """
    restart_count = 0

    if pod.status.container_statuses:
        for container in pod.status.container_statuses:
            restart_count += container.restart_count

    return restart_count


def convert_cpu_to_millicores(cpu_value):
    """
    Kubernetes CPU can come as:
    - 5m   means 5 millicores
    - 1    means 1 CPU core = 1000 millicores
    - 250n means nanocores

    We convert everything into millicores.
    """
    if cpu_value.endswith("m"):
        return int(cpu_value.replace("m", ""))

    if cpu_value.endswith("n"):
        return int(cpu_value.replace("n", "")) / 1_000_000

    return int(cpu_value) * 1000


def convert_memory_to_mib(memory_value):
    """
    Kubernetes memory can come as:
    - Ki
    - Mi
    - Gi

    We convert everything into MiB.
    """
    if memory_value.endswith("Ki"):
        return round(int(memory_value.replace("Ki", "")) / 1024, 2)

    if memory_value.endswith("Mi"):
        return round(int(memory_value.replace("Mi", "")), 2)

    if memory_value.endswith("Gi"):
        return round(int(memory_value.replace("Gi", "")) * 1024, 2)

    return 0


def collect_pod_metrics():
    """
    Collects pod information and pod resource usage.
    """

    core_api = client.CoreV1Api()
    metrics_api = client.CustomObjectsApi()

    pods = core_api.list_pod_for_all_namespaces()

    metrics_response = metrics_api.list_cluster_custom_object(
        group="metrics.k8s.io",
        version="v1beta1",
        plural="pods"
    )

    metrics_map = {}

    for item in metrics_response["items"]:
        namespace = item["metadata"]["namespace"]
        pod_name = item["metadata"]["name"]

        total_cpu = 0
        total_memory = 0

        for container in item["containers"]:
            cpu = container["usage"]["cpu"]
            memory = container["usage"]["memory"]

            total_cpu += convert_cpu_to_millicores(cpu)
            total_memory += convert_memory_to_mib(memory)

        metrics_map[(namespace, pod_name)] = {
            "cpu_millicores": round(total_cpu, 2),
            "memory_mib": round(total_memory, 2)
        }

    collected_data = []

    for pod in pods.items:
        namespace = pod.metadata.namespace
        pod_name = pod.metadata.name

        resource_usage = metrics_map.get(
            (namespace, pod_name),
            {
                "cpu_millicores": 0,
                "memory_mib": 0
            }
        )

        pod_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "namespace": namespace,
            "pod": pod_name,
            "status": pod.status.phase,
            "restart_count": get_pod_restart_count(pod),
            "node": pod.spec.node_name,
            "cpu_millicores": resource_usage["cpu_millicores"],
            "memory_mib": resource_usage["memory_mib"]
        }

        collected_data.append(pod_data)

    return collected_data


def save_metrics(metrics):
    """
    Stores collected metrics in a JSON file.
    Later, you can replace this with database storage.
    """
    with open("pod_metrics.json", "w") as file:
        json.dump(metrics, file, indent=4)


def main():
    load_kubernetes_config()

    while True:
        print("Collecting pod metrics...")

        try:
            metrics = collect_pod_metrics()
            save_metrics(metrics)

            for pod in metrics:
                print(
                    f"{pod['namespace']}/{pod['pod']} | "
                    f"Status: {pod['status']} | "
                    f"CPU: {pod['cpu_millicores']}m | "
                    f"Memory: {pod['memory_mib']}Mi | "
                    f"Restarts: {pod['restart_count']}"
                )

        except Exception as error:
            print("Error while collecting metrics:", error)

        print("-" * 80)
        time.sleep(5)


if __name__ == "__main__":
    main()
