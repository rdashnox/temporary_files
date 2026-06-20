# Fix: `docker` is not recognized

## Problem

When running:

```powershell
.\start-microservices.ps1
```

PowerShell may show:

```text
docker : The term 'docker' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

This means Docker Desktop is not installed, Docker Desktop is not running, or Docker is not added to the Windows PATH.

## Fix included in this package

The project now supports two microservice launch modes:

1. **Docker mode** — production-style containers with Nginx load balancing.
2. **No-Docker local mode** — 12 local Uvicorn processes plus a Python API gateway.

The main script now detects Docker automatically. If Docker is missing, it starts the no-Docker fallback.

```powershell
.\start-microservices.ps1
```

You can also start the no-Docker mode directly:

```powershell
.\start-microservices-local.ps1
```

## Local no-Docker ports

| Service | Node 1 | Node 2 | Node 3 |
|---|---:|---:|---:|
| Auth/Login | 8101 | 8102 | 8103 |
| Order | 8201 | 8202 | 8203 |
| Inventory | 8301 | 8302 | 8303 |
| Notification | 8401 | 8402 | 8403 |
| Python API Gateway | 8000 | - | - |

The frontend should still call:

```text
http://127.0.0.1:8000
```

## Stop local services

```powershell
.\stop-microservices-local.ps1
```

or:

```powershell
.\stop-microservices.ps1
```

## Failover test without Docker

Start services:

```powershell
.\start-microservices-local.ps1
```

Stop one order service node:

```powershell
Stop-Process -Id (Import-Csv .microservices\local-pids.csv | Where-Object name -eq 'order-service-1').pid
```

Then call the gateway again. The gateway will continue routing order requests to `order-service-2` and `order-service-3`.

```powershell
curl http://127.0.0.1:8000/api/v1/service-info
```

## Production recommendation

For actual deployment, install Docker Desktop locally or use a VPS/cloud server with Docker Engine. Docker/Nginx is still the cleaner production deployment because it manages networking, restart policies, and container isolation better than local PowerShell processes.
