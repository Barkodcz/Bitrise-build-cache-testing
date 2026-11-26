"""A "widely depended" core module — uses requests (a real dependency) so poetry install has real
content to resolve/cache."""
import requests


def user_agent_header() -> dict:
    return requests.utils.default_headers()
