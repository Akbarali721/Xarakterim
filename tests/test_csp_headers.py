"""CSP: Telegram WebApp SDK ruxsat etiladi, umumiy himoya saqlanadi."""

from app.config import DEFAULT_CSP


def test_landing_csp_allows_telegram_sdk_script(client):
    response = client.get("/personality")
    assert response.status_code == 200
    csp = response.headers.get("content-security-policy") or response.headers.get(
        "Content-Security-Policy"
    )
    assert csp
    assert "script-src 'self' https://telegram.org" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp


def test_default_csp_constant_matches_runtime_header_shape():
    assert "https://telegram.org" in DEFAULT_CSP
    assert "script-src 'self'" in DEFAULT_CSP
