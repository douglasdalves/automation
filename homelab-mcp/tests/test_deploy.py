from subprocess import CompletedProcess

from app.services.deploy import deploy


def test_deploy_only_pulls_repository(monkeypatch, tmp_path):
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append((cmd, kwargs["cwd"]))
        return CompletedProcess(cmd, 0, stdout="updated", stderr="")

    monkeypatch.setattr("app.services.deploy.subprocess.run", fake_run)
    monkeypatch.setenv("DEPLOY_REPOSITORY_DIR", str(tmp_path))

    result = deploy()

    assert result["success"] is True
    assert commands == [(["git", "pull", "--ff-only"], tmp_path)]


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