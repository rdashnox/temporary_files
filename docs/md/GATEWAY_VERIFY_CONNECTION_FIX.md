# Gateway Verification Connection Fix

## Problem

The verifier may show:

```powershell
Invoke-RestMethod : Unable to connect to the remote server
```

This happens when `verify-checkout-admin-order-list.ps1` reads a stale URL from `frontend\.env.local`, for example:

```text
http://127.0.0.1:18004/api/v1
```

but the local API gateway is actually stopped or running on another fallback port.

## Fix

The verifier now auto-detects the running gateway from:

1. `.microservices\api-base-url.txt`
2. `.microservices\local-pids.csv`
3. `frontend\.env.local`
4. common ports `8000` and `18000` to `18030`

It tests `/api/v1/health` before attempting login.

## Correct workflow

```powershell
.\stop-microservices-local.ps1
.\start-microservices-local-mysql.ps1
.\verify-checkout-admin-order-list.ps1
```

Or let the verifier start the services when no gateway is running:

```powershell
.\verify-checkout-admin-order-list.ps1 -StartIfDown
```

## Manual override

If your startup script prints a gateway URL such as:

```text
http://127.0.0.1:18001/api/v1
```

run:

```powershell
.\verify-checkout-admin-order-list.ps1 -ApiBase http://127.0.0.1:18001/api/v1
```
