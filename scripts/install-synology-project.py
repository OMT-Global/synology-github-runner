#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ConnectionConfig:
    host: str
    port: str
    username: str
    password: str
    secure: bool
    cert_verify: bool
    dsm_version: int
    api_repo: str


@dataclass
class ProjectConfig:
    name: str
    directory: str
    compose_file_name: str
    env_file_name: str
    log_file_name: str


def main() -> int:
    plan = json.load(sys.stdin)
    connection = ConnectionConfig(
        host=plan["connection"]["host"],
        port=plan["connection"]["port"],
        username=plan["connection"]["username"],
        password=plan["connection"]["password"],
        secure=bool(plan["connection"]["secure"]),
        cert_verify=bool(plan["connection"]["certVerify"]),
        dsm_version=int(plan["connection"]["dsmVersion"]),
        api_repo=plan["connection"]["apiRepo"],
    )
    project = ProjectConfig(
        name=plan["project"]["name"],
        directory=plan["project"]["directory"],
        compose_file_name=plan["project"]["composeFileName"],
        env_file_name=plan["project"]["envFileName"],
        log_file_name=plan["project"]["logFileName"],
    )
    options = plan["options"]
    deployment_script = plan["deploymentScript"]
    compose_content = plan["composeContent"]
    env_file_content = plan["envFileContent"]

    _import_synology_api(connection.api_repo)
    from synology_api.docker_api import Docker
    from synology_api.filestation import FileStation
    from synology_api.task_scheduler import TaskScheduler

    kwargs = {
        "ip_address": connection.host,
        "port": connection.port,
        "username": connection.username,
        "password": connection.password,
        "secure": connection.secure,
        "cert_verify": connection.cert_verify,
        "dsm_version": connection.dsm_version,
        "debug": False,
    }

    file_station = FileStation(**kwargs, interactive_output=False)
    scheduler = TaskScheduler(**kwargs)
    docker = Docker(**kwargs)

    task_id: int | None = None
    try:
        remote_log_path = f"{project.directory}/logs/{project.log_file_name}"
        _upload_project_files(
            file_station=file_station,
            project=project,
            compose_content=compose_content,
            env_file_content=env_file_content,
        )
        task_name = f"codex-install-{project.name}-{int(time.time())}"
        task = scheduler.create_script_task(
            task_name=task_name,
            owner="root",
            script=deployment_script,
            enable=True,
            run_frequently=False,
            run_date=_today_for_scheduler(),
            repeat="no_repeat",
            start_time_h=datetime.now().hour,
            start_time_m=datetime.now().minute,
        )
        task_id = int(task["data"]["id"])
        scheduler.task_run(task_id=task_id, real_owner="root")
        task_result = _wait_for_task_result(scheduler, task_id, timeout_seconds=300)
        project_state = _find_project_state(docker, project.name)

        if int(task_result.get("exit_code", 1)) != 0:
            raise RuntimeError(
                f"installer task failed with exit_code={task_result.get('exit_code')} "
                f"see {remote_log_path}"
            )

        payload = {
            "ok": True,
            "project": project_state,
            "task": {
                "id": task_id,
                "result": task_result,
            },
            "remoteLogPath": remote_log_path,
            "options": options,
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        return 0
    finally:
        if task_id is not None:
            try:
                scheduler.task_delete(task_id=task_id, real_owner="root")
            except Exception:
                pass
        try:
            docker.logout()
        except Exception:
            pass
        try:
            file_station.logout()
        except Exception:
            pass


def _import_synology_api(repo_path: str) -> None:
    resolved = str(Path(repo_path).expanduser().resolve())
    if not Path(resolved).exists():
        raise FileNotFoundError(
            f"synology-api repo not found at {resolved}; set SYNOLOGY_API_REPO"
        )
    if resolved not in sys.path:
        sys.path.insert(0, resolved)


def _upload_project_files(
    *,
    file_station: Any,
    project: ProjectConfig,
    compose_content: str,
    env_file_content: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="synology-runner-install-") as temp_dir:
        local_compose = Path(temp_dir) / project.compose_file_name
        local_env = Path(temp_dir) / project.env_file_name
        local_compose.write_text(compose_content, encoding="utf-8")
        local_env.write_text(env_file_content, encoding="utf-8")

        compose_result = file_station.upload_file(
            dest_path=project.directory,
            file_path=str(local_compose),
            create_parents=True,
            overwrite=True,
            progress_bar=False,
        )
        env_result = file_station.upload_file(
            dest_path=project.directory,
            file_path=str(local_env),
            create_parents=True,
            overwrite=True,
            progress_bar=False,
        )

        for result in (compose_result, env_result):
            if isinstance(result, tuple):
                raise RuntimeError(
                    f"failed to upload project files: status={result[0]} body={result[1]}"
                )


def _wait_for_task_result(
    scheduler: Any, task_id: int, timeout_seconds: int
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = scheduler.get_task_results(task_id=task_id)
        entries = response.get("data", [])
        if entries:
            return entries[0]
        time.sleep(2)

    raise TimeoutError(
        f"timed out waiting for Task Scheduler result for task {task_id}"
    )


def _find_project_state(docker: Any, project_name: str) -> dict[str, Any] | None:
    response = docker.list_projects()
    projects = response.get("data", {})
    for project in projects.values():
        if isinstance(project, dict) and project.get("name") == project_name:
            return {
                "id": project.get("id"),
                "name": project.get("name"),
                "status": project.get("status"),
                "path": project.get("path"),
                "updated_at": project.get("updated_at"),
            }
    return None


def _today_for_scheduler() -> str:
    now = datetime.now()
    return f"{now.year}/{now.month}/{now.day}"


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        sys.stderr.write(f"{error}\n")
        raise SystemExit(1)
