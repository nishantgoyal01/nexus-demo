class MemoryAgent:
    def __init__(self):
        self.name = "MemoryAgent"
        self.warning_threshold = 70
        self.critical_threshold = 85

    def analyze(self, metric):
        memory = metric.get("memory", metric.get("memory_mib", 0))
        pod = metric.get("pod")
        namespace = metric.get("namespace")

        if memory >= self.critical_threshold:
            return {
                "agent": self.name,
                "severity": "critical",
                "pod": pod,
                "namespace": namespace,
                "message": f"Memory pressure detected in {pod}. Memory usage is {memory}%."
            }

        if memory >= self.warning_threshold:
            return {
                "agent": self.name,
                "severity": "warning",
                "pod": pod,
                "namespace": namespace,
                "message": f"High memory usage in {pod}. Memory usage is {memory}%."
            }

        return None