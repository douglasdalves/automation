from subprocess import CompletedProcess

from app.services.deploy import deploy


def test_deploy_pulls_then_restarts_services(monkeypatch, tmp_path):
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        return CompletedProcess(cmd, 0, stdout="updated", stderr="")

    monkeypatch.setattr("app.services.deploy.subprocess.run", fake_run)
    monkeypatch.setenv("DEPLOY_REPOSITORY_DIR", str(tmp_path))

    result = deploy()

    assert result["success"] is True
    assert commands == [
        ["git", "pull", "--ff-only"],
        ["sudo", "mkdir", "-p", "/etc/app-config-sync"],
        [
            "sudo",
            "cp",
            str(tmp_path / "configs-apps" / "app-config-sync" / "sync.conf"),
            "/etc/app-config-sync/sync.conf",
        ],
        [
            "sudo",
            "cp",
            str(tmp_path / "configs-apps" / "app-config-sync" / "sync-configs.sh"),
            "/usr/local/bin/sync-configs.sh",
        ],
        ["sudo", "chmod", "+x", "/usr/local/bin/sync-configs.sh"],
        [
            "sudo",
            "cp",
            str(tmp_path / "configs-apps" / "app-config-sync" / "app-config-sync.service"),
            str(tmp_path / "configs-apps" / "app-config-sync" / "app-config-sync.path"),
            "/etc/systemd/system/",
        ],
        ["sudo", "systemctl", "daemon-reload"],
        ["sudo", "systemctl", "enable", "--now", "app-config-sync.path"],
        ["sudo", "systemctl", "start", "app-config-sync.service"],
        ["sudo", "systemctl", "restart", "homelab-telegram-bot"],
        ["sudo", "systemctl", "restart", "homelab-mcp"],
    ]
    assert result["restarted_services"] == [
        "homelab-telegram-bot",
        "homelab-mcp",
    ]


def test_deploy_reports_pull_failure(monkeypatch, tmp_path):
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        return CompletedProcess(cmd, 1, stdout="", stderr="conflict")

    monkeypatch.setattr("app.services.deploy.subprocess.run", fake_run)
    monkeypatch.setenv("DEPLOY_REPOSITORY_DIR", str(tmp_path))

    result = deploy()

    assert result == {
        "success": False,
        "step": "git_pull",
        "error": "conflict",
    }
    assert commands == [["git", "pull", "--ff-only"]]


def test_deploy_reports_restart_failure(monkeypatch, tmp_path):
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        if cmd[:2] == ["sudo", "systemctl"] and cmd[-1] == "homelab-mcp":
            return CompletedProcess(cmd, 1, stdout="", stderr="MCP restart failed")
        return CompletedProcess(cmd, 0, stdout="updated", stderr="")

    monkeypatch.setattr("app.services.deploy.subprocess.run", fake_run)
    monkeypatch.setenv("DEPLOY_REPOSITORY_DIR", str(tmp_path))

    result = deploy()

    assert result == {
        "success": False,
        "step": "restart_service",
        "service": "homelab-mcp",
        "restarted_services": ["homelab-telegram-bot"],
        "error": "MCP restart failed",
    }
    assert commands == [
        ["git", "pull", "--ff-only"],
        ["sudo", "mkdir", "-p", "/etc/app-config-sync"],
        [
            "sudo",
            "cp",
            str(tmp_path / "configs-apps" / "app-config-sync" / "sync.conf"),
            "/etc/app-config-sync/sync.conf",
        ],
        [
            "sudo",
            "cp",
            str(tmp_path / "configs-apps" / "app-config-sync" / "sync-configs.sh"),
            "/usr/local/bin/sync-configs.sh",
        ],
        ["sudo", "chmod", "+x", "/usr/local/bin/sync-configs.sh"],
        [
            "sudo",
            "cp",
            str(tmp_path / "configs-apps" / "app-config-sync" / "app-config-sync.service"),
            str(tmp_path / "configs-apps" / "app-config-sync" / "app-config-sync.path"),
            "/etc/systemd/system/",
        ],
        ["sudo", "systemctl", "daemon-reload"],
        ["sudo", "systemctl", "enable", "--now", "app-config-sync.path"],
        ["sudo", "systemctl", "start", "app-config-sync.service"],
        ["sudo", "systemctl", "restart", "homelab-telegram-bot"],
        ["sudo", "systemctl", "restart", "homelab-mcp"],
    ]