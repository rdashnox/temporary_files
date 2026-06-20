"""Locust load test for 1,000 active FinMark users.

Recommended command:
    locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 --users 1000 --spawn-rate 50 --run-time 10m
"""

from __future__ import annotations

import os
import random
from uuid import uuid4

from locust import HttpUser, between, task

LOADTEST_USER_COUNT = int(os.getenv("LOADTEST_USER_COUNT", "1000"))
LOADTEST_PASSWORD = os.getenv("LOADTEST_PASSWORD", "LoadTest123!")
DEMO_FALLBACK_USER = os.getenv("LOADTEST_FALLBACK_USER", "user@example.com")
DEMO_FALLBACK_PASSWORD = os.getenv("LOADTEST_FALLBACK_PASSWORD", "Password123!")


class FinMarkActiveUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self) -> None:
        self.access_token = None
        self.products = []
        self.login()

    def _auth_headers(self, extra: dict | None = None) -> dict:
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        if extra:
            headers.update(extra)
        return headers

    def login(self) -> None:
        number = random.randint(1, LOADTEST_USER_COUNT)
        username = f"loadtest{number:04d}@example.com"
        response = self.client.post(
            "/api/v1/auth/token",
            data={"username": username, "password": LOADTEST_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            name="auth/token loadtest user",
        )
        if response.status_code != 200:
            response = self.client.post(
                "/api/v1/auth/token",
                data={"username": DEMO_FALLBACK_USER, "password": DEMO_FALLBACK_PASSWORD},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                name="auth/token fallback user",
            )
        response.raise_for_status()
        self.access_token = response.json()["access_token"]

    @task(7)
    def browse_products(self) -> None:
        response = self.client.get(
            "/api/v1/inventory/products",
            headers=self._auth_headers(),
            name="inventory/products",
        )
        if response.status_code == 200:
            self.products = response.json()

    @task(2)
    def read_notifications(self) -> None:
        self.client.get(
            "/api/v1/notifications?limit=10",
            headers=self._auth_headers(),
            name="notifications/list",
        )

    @task(1)
    def checkout_one_item(self) -> None:
        if not self.products:
            self.browse_products()
        if not self.products:
            return

        product = random.choice(self.products)
        idempotency_key = f"locust-{uuid4()}"
        payload = {
            "customer_name": "Load Test User",
            "delivery_address": "1000 Scale Test Street, Manila",
            "payment_method": "Cash on Delivery",
            "idempotency_key": idempotency_key,
            "items": [{"product_id": product["id"], "quantity": 1}],
        }
        self.client.post(
            "/api/v1/orders/checkout",
            json=payload,
            headers=self._auth_headers({"Idempotency-Key": idempotency_key}),
            name="orders/checkout",
        )
