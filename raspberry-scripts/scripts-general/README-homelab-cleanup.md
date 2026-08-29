# Homelab Cleanup

`homelab-cleanup.sh` is a conservative maintenance script for the Raspberry Pi / CasaOS host. Its default mode is a preview; it does not change anything until `--apply` is supplied.

It only performs these actions:

- clears the APT package cache;
- removes dangling Docker images;
- reports stopped Docker containers; removal requires an explicit option;
- removes archived systemd journal files older than seven days;
- removes old VS Code Server `Stable-<commit>` folders only after identifying and preserving the active commit from `agent-host-stable.log`.

It never calls Docker volume pruning, removes Docker images in use, changes `/DATA/AppData`, or directly removes anything from containerd.

## First run

Copy the script to the Pi, make it executable, and preview the work:

```bash
chmod 750 homelab-cleanup.sh
sudo ./homelab-cleanup.sh --dry-run --vscode-user dalves
```

Review the list, especially the inactive VS Code Server folders. Then apply it:

```bash
sudo ./homelab-cleanup.sh --apply --vscode-user dalves
```

To also remove stopped containers, opt in on that particular run:

```bash
sudo ./homelab-cleanup.sh --apply --prune-stopped-containers --vscode-user dalves
```

Removing a container does not remove Docker volumes or host bind mounts, but it does remove the container definition and its writable layer. For that reason it is not enabled by default, including in cron.

The VS Code cleanup safely skips itself if it cannot find a valid active commit. For extra caution, run the first applied cleanup after closing any active VS Code Remote SSH connection.

## Cron and alert hook

For unattended runs, copy `homelab-cleanup.conf.example` to `/etc/homelab-cleanup.conf`, set `VSCODE_USER`, and restrict it to root:

```bash
sudo install -m 600 -o root -g root homelab-cleanup.conf.example /etc/homelab-cleanup.conf
```

Example monthly root crontab entry (03:30 on the first day):

```cron
30 3 1 * * /usr/local/sbin/homelab-cleanup.sh --apply >> /var/log/homelab-cleanup.log 2>&1
```

The report emits an alert once the root filesystem is at or above 70% (configurable). It can call an existing Telegram wrapper through `ALERT_COMMAND`; the bot-specific command is intentionally not guessed until its actual script/configuration is reviewed.
