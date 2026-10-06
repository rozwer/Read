from local_readable.security import is_loopback_host


def test_only_loopback_urls_are_accepted():
    assert is_loopback_host("http://127.0.0.1:11434")
    assert is_loopback_host("http://localhost:11434")
    assert is_loopback_host("http://[::1]:11434")
    assert not is_loopback_host("https://api.openai.com")
    assert not is_loopback_host("http://192.168.1.10:11434")

