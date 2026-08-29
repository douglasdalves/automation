from subprocess import CompletedProcess

from app.services.docker import (
    inspect_container,
    list_compose_files,
    list_containers,
    manage_container,
    start_compose_file,
)


def test_list_containers_parses_docker_ps_output(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True, check=False):
        assert cmd[:2] == ["docker", "ps"]
        return CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="CONTAINER ID\tIMAGE\tSTATUS\tNAMES\nabc123\tnginx:latest\tUp 2 days\tweb\n",
            stderr="",
        )

    monkeypatch.setattr("app.services.docker.subprocess.run", fake_run)

    result = list_containers(all_containers=False)

    assert result["success"] is True
    assert result["containers"][0]["id"] == "abc123"
    assert result["containers"][0]["name"] == "web"
    assert result["containers"][0]["status"] == "Up 2 days"


def test_inspect_container_returns_formatted_details(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True, check=False):
        assert cmd[:2] == ["docker", "inspect"]
        return CompletedProcess(
            args=cmd,
            returncode=0,
            stdout='[{"Name":"/web","State":{"Status":"running"},"Config":{"Image":"nginx:latest"}}]',
            stderr="",
        )

    monkeypatch.setattr("app.services.docker.subprocess.run", fake_run)

    result = inspect_container("web")

    assert result["success"] is True
    assert result["container"]["name"] == "web"
    assert result["container"]["image"] == "nginx:latest"
    assert result["container"]["status"] == "running"


def test_manage_container_reports_command_errors(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True, check=False):
        return CompletedProcess(args=cmd, returncode=127, stdout="", stderr="docker: not found")

    monkeypatch.setattr("app.services.docker.subprocess.run", fake_run)

    result = manage_container("web", "start")

    assert result["success"] is False
    assert "docker" in result["error"].lower()


def test_docker_reruns_with_sudo_on_permission_error(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True, check=False):
        if cmd[:1] == ["docker"]:
            return CompletedProcess(args=cmd, returncode=1, stdout="", stderr="permission denied while trying to connect to the docker daemon socket")
        if cmd[:2] == ["sudo", "-n"]:
            return CompletedProcess(args=cmd, returncode=0, stdout="CONTAINER ID\nabc123\n", stderr="")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr("app.services.docker.subprocess.run", fake_run)
    monkeypatch.setattr("app.services.docker.shutil.which", lambda name: "/usr/bin/sudo")

    result = list_containers()

    assert result["success"] is True
    assert result["containers"][0]["id"] == "abc123"


def test_list_containers_parses_space_separated_output(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True, check=False):
        return CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="CONTAINER ID IMAGE STATUS NAMES\nabc123 nginx:latest Up 2 days web\n",
            stderr="",
        )

    monkeypatch.setattr("app.services.docker.subprocess.run", fake_run)

    result = list_containers()

    assert result["success"] is True
    assert result["containers"][0]["id"] == "abc123"
    assert result["containers"][0]["name"] == "web"


def test_list_compose_files_lists_only_allowed_yaml_files(monkeypatch):
    allowed_dir = "/tmp/automation/dc-local"
    monkeypatch.setattr("app.services.docker.Path", lambda *parts: __import__("pathlib").Path(*parts))

    def fake_iterdir(path):
        assert str(path) == allowed_dir
        return [
            __import__("pathlib").Path("/tmp/automation/dc-local/dc-compose-filebrowser.yaml"),
            __import__("pathlib").Path("/tmp/automation/dc-local/notes.txt"),
            __import__("pathlib").Path("/tmp/automation/dc-local/.hidden.yml"),
            __import__("pathlib").Path("/tmp/automation/dc-local/other.yaml.bak"),
        ]

    monkeypatch.setattr("app.services.docker._get_compose_directory", lambda: __import__("pathlib").Path(allowed_dir))
    monkeypatch.setattr("pathlib.Path.iterdir", fake_iterdir)

    result = list_compose_files()

    assert result["success"] is True
    assert result["files"] == ["dc-compose-filebrowser.yaml"]


def test_start_compose_file_rejects_invalid_file_name(monkeypatch):
    result = start_compose_file("../etc/passwd")

    assert result["success"] is False
    assert "inválido" in result["error"].lower()


def test_start_compose_file_runs_docker_compose(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True, check=False, cwd=None):
        assert cmd[:3] == ["docker", "compose", "-f"]
        assert cmd[3].endswith("dc-compose-filebrowser.yaml")
        assert cmd[4:] == ["up", "-d"]
        assert cwd == "/tmp/automation/dc-local"
        return CompletedProcess(args=cmd, returncode=0, stdout="done", stderr="")

    monkeypatch.setattr("app.services.docker._get_compose_directory", lambda: __import__("pathlib").Path("/tmp/automation/dc-local"))
    monkeypatch.setattr("app.services.docker.subprocess.run", fake_run)

    result = start_compose_file("dc-compose-filebrowser.yaml")

    assert result["success"] is True
    assert result["file_name"] == "dc-compose-filebrowser.yaml"
