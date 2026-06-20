# FinMark Load Testing Guide

This folder tests whether the app can support **1,000 active users** browsing products, reading notifications, and placing orders.

## 1. Prepare the database

Use MySQL/PostgreSQL for load testing. Do not use SQLite for 1,000 active users.

```powershell
python -m backend.scripts.seed_load_test_users --count 1000
```

This creates:

```text
loadtest0001@example.com to loadtest1000@example.com
Password: LoadTest123!
```

## 2. Install Locust

```powershell
python -m pip install -r loadtests/requirements-loadtest.txt
```

## 3. Start the backend in production-like mode

Linux/VPS:

```bash
bash start-production-linux.sh
```

Windows/dev fallback:

```powershell
.\start-production-api.ps1
```

## 4. Run a 1,000-user test

```powershell
locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 --users 1000 --spawn-rate 50 --run-time 10m
```

Open the Locust UI at:

```text
http://127.0.0.1:8089
```


## Microservice mode target

For the 3-node microservice deployment, start the gateway first:

```powershell
.\start-microservices.ps1
```

Then run Locust against the gateway. The host stays the same because the microservice Nginx gateway is mapped to port `8000`:

```powershell
locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 --users 1000 --spawn-rate 50 --run-time 10m
```

During the test, you may stop one node such as `order-service-1`. The target result is that requests continue through `order-service-2` and `order-service-3`.

## Target acceptance numbers

For a class/demo production target, aim for:

- Error rate: below 1%
- Product browsing p95 latency: below 500 ms
- Checkout p95 latency: below 1,500 ms
- Login p95 latency: below 1,000 ms
- API CPU sustained: below 75%
- Database CPU sustained: below 70%

If checkout latency is high, scale database first, then increase API workers.
