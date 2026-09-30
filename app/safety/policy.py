import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class SafetyPolicy:
    allowed_hosts: frozenset[str] = frozenset(
        {urlparse(os.getenv("NORTHSTAR_URL", "http://localhost:5173")).netloc}
    )
    allowed_actions: frozenset[str] = frozenset(
        {
            "fill",
            "click",
            "press_key",
            "wait",
            "assert",
            "extract",
        }
    )

    def check_url(self, url: str) -> None:
        parsed = urlparse(url)
        host = parsed.netloc

        if host not in self.allowed_hosts:
            raise PermissionError(
                f"Blocked navigation to disallowed host: {host or url}"
            )

    def check_action(self, action_type: str) -> None:
        if action_type not in self.allowed_actions:
            raise PermissionError(
                f"Blocked action type by safety policy: {action_type}"
            )
