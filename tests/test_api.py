"""HTTP contract checks; no database, GPU or HeteroES instance required."""

import httpx
from fastapi.testclient import TestClient

from app.app import app

client = TestClient(app)


def test_hello_and_student_routes():
    hello = client.get("/hello")
    assert hello.status_code == 200
    assert hello.json() == {"message": "Hello from MiniCloud!"}

    students = client.get("/student")
    assert students.status_code == 200
    assert len(students.json()) == 5


def test_own_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "minicloud-app"}


def test_database_unavailable_without_configuration(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = client.get("/students-db")
    assert response.status_code == 503
    assert response.json() == {"error": "database unavailable"}


def test_heteroes_integration_disabled_by_default(monkeypatch):
    monkeypatch.delenv("HETEROES_HEALTH_URL", raising=False)
    response = client.get("/heteroes-health")
    assert response.status_code == 503
    assert response.json() == {"status": "not configured"}


def test_heteroes_health_is_only_a_read_only_reachability_probe(monkeypatch):
    monkeypatch.setenv("HETEROES_HEALTH_URL", "http://isolated-lab:8123/api/v1/health")
    called = {}

    def fake_get(url, *, timeout, follow_redirects):
        called.update(url=url, timeout=timeout, follow_redirects=follow_redirects)
        return httpx.Response(200, json={"status": "ok"})

    monkeypatch.setattr(httpx, "get", fake_get)
    response = client.get("/heteroes-health")
    assert response.status_code == 200
    assert response.json() == {"status_code": 200, "reachable": True}
    assert called == {
        "url": "http://isolated-lab:8123/api/v1/health",
        "timeout": 3,
        "follow_redirects": False,
    }


def test_heteroes_health_does_not_follow_redirects(monkeypatch):
    monkeypatch.setenv("HETEROES_HEALTH_URL", "http://isolated-lab:8123/api/v1/health")

    def fake_get(url, *, timeout, follow_redirects):
        return httpx.Response(302, headers={"location": "https://elsewhere.example"})

    monkeypatch.setattr(httpx, "get", fake_get)
    response = client.get("/heteroes-health")
    assert response.status_code == 502
    assert response.json() == {"status_code": 302, "reachable": False}
