from showcase_poetry.core import user_agent_header


def test_user_agent_header():
    headers = user_agent_header()
    assert "User-Agent" in headers
