from app.services.health import health_check


def test_health_includes_temperature_and_running_containers(monkeypatch):
    monkeypatch.setattr("app.services.health.cpu_temperature", lambda: 42.1)

    def fake_list_containers(all_containers=False):
        return {
            "success": True,
            "containers": [
                {"id": "abc123", "name": "web", "status": "Up 2 days"},
            ],
        }

    monkeypatch.setattr("app.services.health.list_containers", fake_list_containers)

    result = health_check()

    assert result["cpu"]["temperature"] == 42.1
    assert result["docker"]["running_containers"][0]["name"] == "web"
