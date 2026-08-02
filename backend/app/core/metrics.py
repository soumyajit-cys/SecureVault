import threading
import time
from collections import defaultdict

_lock = threading.Lock()

_request_count: defaultdict[str, int] = (
    defaultdict(int)
)

_error_count: defaultdict[str, int] = (
    defaultdict(int)
)

_latency_total: defaultdict[str, float] = (
    defaultdict(float)
)

_start_time: float = time.monotonic()


def record_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
):

    route = (
        path or "unhandled"
    )

    with _lock:

        _request_count[route] += 1
        _latency_total[route] += (
            duration_ms
        )

        if status_code >= 500:
            _error_count[route] += 1


def render_metrics() -> str:
    """
    Render in-memory metrics in Prometheus
    text exposition format.
    """
    uptime_seconds = time.monotonic() - _start_time

    lines = [
        (
            "# HELP vault_requests_total "
            "Total number of requests handled."
        ),
        "# TYPE vault_requests_total counter",
    ]

    for route, count in sorted(
        _request_count.items()
    ):

        lines.append(
            'vault_requests_total'
            f'{{path="{route}"}} '
            f"{count}"
        )

    lines.append(
        "# HELP vault_request_duration_ms "
        "Request latency."
    )
    lines.append(
        "# TYPE vault_request_duration_ms histogram"
    )

    for route, total in sorted(
        _latency_total.items()
    ):

        count = _request_count.get(
            route, 0
        )

        lines.append(
            "vault_request_duration_ms_sum"
            f'{{path="{route}"}} '
            f"{total:.3f}"
        )
        lines.append(
            "vault_request_duration_ms_count"
            f'{{path="{route}"}} '
            f"{count}"
        )

    lines.append(
        "# HELP secure_errors_total "
        "Total number of 5xx responses."
    )
    lines.append(
        "# TYPE secure_errors_total counter"
    )

    for route, count in sorted(
        _error_count.items()
    ):

        lines.append(
            'secure_errors_total'
            f'{{path="{route}"}} '
            f"{count}"
        )

    lines.append(
        "# HELP secure_uptime_seconds "
        "Process uptime."
    )
    lines.append(
        "# TYPE secure_uptime_seconds gauge"
    )
    lines.append(
        "secure_uptime_seconds "
        f"{uptime_seconds:.0f}"
    )

    return "\n".join(lines) + "\n"