# Windows Socket Error 10013 Fix

## Error

```text
[WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions
```

## Cause

This is a Windows port-binding problem. It usually happens when one of these ports is blocked, reserved, protected, or already used by another process:

- `8000` API gateway/backend
- `8101-8103` Auth service replicas
- `8201-8203` Order service replicas
- `8301-8303` Inventory service replicas
- `8401-8403` Notification service replicas

Common Windows causes:

1. The port is inside a Windows excluded TCP port range.
2. Another process already owns the port.
3. Security software or firewall blocks the bind operation.
4. Old FinMark Uvicorn processes were left running from a previous start.

## What was changed

The project now includes a Windows-safe port launcher:

- probes each port before starting Uvicorn;
- automatically uses fallback ports such as `18000`, `18101`, `18201`, etc.;
- writes the selected gateway URL to `frontend/.env.local`;
- passes dynamic service-node ports to the local gateway through `SERVICE_POOLS_JSON`;
- stops old local microservice processes before starting a new set;
- includes a diagnostic script.

## Recommended commands

```powershell
.\stop-microservices-local.ps1
.\start-microservices-local.ps1
```

If you want to inspect the Windows port issue:

```powershell
.\diagnose-windows-ports.ps1
```

If the script uses a gateway port other than `8000`, restart the frontend:

```powershell
cd frontend
npm run dev
```

Then open the exact gateway URL printed by the startup script, for example:

```text
http://127.0.0.1:18000/api/v1/health
```

## Manual Windows commands

Show excluded Windows TCP port ranges:

```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

Check who is using port 8000:

```powershell
netstat -ano | findstr :8000
```

Kill a process by PID:

```powershell
Stop-Process -Id <PID> -Force
```
