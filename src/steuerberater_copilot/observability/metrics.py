"""In-process basic runtime metrics for local and demo deployments."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuntimeMetrics:
    """Mutable counters for demo-scale runtime and quality signals.

    Metrics are process-local and intentionally minimal. They do not claim
    productive SRE coverage or cloud-vendor lock-in.
    """

    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    provider_error_count: int = 0
    parse_error_count: int = 0
    validation_error_count: int = 0
    abstention_count: int = 0
    contradiction_count: int = 0
    latencies_ms: list[float] = field(default_factory=list)

    def record_request(
        self,
        *,
        success: bool,
        duration_ms: float,
        provider_error: bool = False,
        parse_error: bool = False,
        validation_error: bool = False,
        abstained: bool = False,
        contradiction: bool = False,
    ) -> None:
        if type(duration_ms) is not float:
            raise TypeError("duration_ms must be a float.")
        if duration_ms < 0:
            raise ValueError("duration_ms must not be negative.")
        self.request_count += 1
        self.latencies_ms.append(duration_ms)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        if provider_error:
            self.provider_error_count += 1
        if parse_error:
            self.parse_error_count += 1
        if validation_error:
            self.validation_error_count += 1
        if abstained:
            self.abstention_count += 1
        if contradiction:
            self.contradiction_count += 1

    @property
    def success_rate(self) -> float | None:
        if self.request_count == 0:
            return None
        return self.success_count / self.request_count

    @property
    def error_rate(self) -> float | None:
        if self.request_count == 0:
            return None
        return self.error_count / self.request_count

    @property
    def abstention_rate(self) -> float | None:
        if self.request_count == 0:
            return None
        return self.abstention_count / self.request_count

    @property
    def p95_latency_ms(self) -> float | None:
        if not self.latencies_ms:
            return None
        ordered = sorted(self.latencies_ms)
        index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
        return ordered[index]

    def snapshot(self) -> dict[str, object]:
        return {
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "provider_error_count": self.provider_error_count,
            "parse_error_count": self.parse_error_count,
            "validation_error_count": self.validation_error_count,
            "abstention_count": self.abstention_count,
            "abstention_rate": self.abstention_rate,
            "contradiction_count": self.contradiction_count,
            "p95_latency_ms": self.p95_latency_ms,
            "estimated_model_cost": None,
        }


DEFAULT_RUNTIME_METRICS = RuntimeMetrics()
