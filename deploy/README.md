# Deployment helpers

This folder contains VM/demo helper scripts and `systemd` unit file templates you can copy to a VM.

Files included:

- `finnie-backend.service` — `systemd` unit for the FastAPI backend (uvicorn).
- `finnie-frontend.service` — `systemd` unit for the Streamlit frontend.
- `run_services.sh` — optional wrapper that starts both services and writes PID/logs.
- `run_vm_ubuntu.sh` — helper to bootstrap a venv and run uvicorn on Ubuntu.
- `run_vm_windows.ps1` — PowerShell helper for Windows.
- `run_ngrok.sh` — helper to start an ngrok tunnel to a local port.

Copy any `.service` file to `/etc/systemd/system/` on your VM, then `systemctl daemon-reload` and `systemctl enable --now <service>`.

Example usage (on VM):

```bash
sudo mv finnie-backend.service /etc/systemd/system/
sudo mv finnie-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now finnie-backend finnie-frontend
sudo journalctl -u finnie-backend -f
```

If Explorer still doesn't show these files after copying, refresh or restart VS Code.
