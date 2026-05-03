import importlib
import sys
import types
import unittest
from datetime import datetime
from unittest.mock import patch


class MerchantPaymentApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._install_fake_psycopg2()
        import database

        cls._original_init_connection_pool = database.init_connection_pool
        database.init_connection_pool = lambda *args, **kwargs: None

        if "app" in sys.modules:
            del sys.modules["app"]

        try:
            cls.app_module = importlib.import_module("app")
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest(f"App dependencies are not installed locally: {exc.name}") from exc
        finally:
            database.init_connection_pool = cls._original_init_connection_pool

        cls.merchant_module = importlib.import_module("merchant_payments")
        cls.client = cls.app_module.app.test_client()

    @classmethod
    def _install_fake_psycopg2(cls):
        if "psycopg2" in sys.modules:
            return

        fake_psycopg2 = types.ModuleType("psycopg2")
        fake_pool_module = types.ModuleType("psycopg2.pool")
        fake_pool_module.SimpleConnectionPool = object
        fake_psycopg2.pool = fake_pool_module

        sys.modules["psycopg2"] = fake_psycopg2
        sys.modules["psycopg2.pool"] = fake_pool_module

    def setUp(self):
        self.store = FakeMerchantStore()
        self.execute_query_patch = patch.object(
            self.merchant_module,
            "execute_query",
            side_effect=self.store.execute_query,
        )
        self.api_key_patch = patch.object(
            self.merchant_module,
            "generate_merchant_api_key",
            return_value="vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4",
        )
        self.execute_query_patch.start()
        self.api_key_patch.start()

    def tearDown(self):
        self.api_key_patch.stop()
        self.execute_query_patch.stop()

    def test_merchant_registration_returns_api_key(self):
        response = self.client.post(
            "/api/v1/merchants/register",
            json={
                "name": "Demo Shop",
                "email": "shop@example.com",
                "password": "password123",
            },
        )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["api_key"], "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4")
        self.assertEqual(body["merchant"]["api_key"], "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4")
        self.assertEqual(body["debug_info"]["password"], "password123")
        self.assertNotIn("plaintext_password", body["debug_info"])

    def test_merchant_ui_pages_render(self):
        login_response = self.client.get("/merchant/login")
        register_response = self.client.get("/merchant/register")
        dashboard_response = self.client.get("/merchant/dashboard")

        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b"Merchant sign in", login_response.data)
        self.assertEqual(register_response.status_code, 200)
        self.assertIn(b"Create merchant", register_response.data)
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertIn(b"Merchant Console", dashboard_response.data)

    def test_merchant_login_returns_jwt_and_api_key(self):
        response = self.client.post(
            "/api/v1/merchants/login",
            json={"email": "shop@example.com", "password": "password123"},
        )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["api_key"], "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4")
        self.assertTrue(body["token"])

    def test_successful_charge_debits_card_and_creates_records(self):
        response = self.client.post(
            "/api/v1/payments/charge",
            headers={"X-Merchant-Api-Key": "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"},
            json={
                "amount": 25.50,
                "currency": "USD",
                "card_number": "4111111111111111",
                "cvv": "123",
                "expiry_date": "12/28",
                "merchant_order_id": "ORDER-1001",
                "description": "Demo checkout",
            },
        )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["payment"]["status"], "completed")
        self.assertEqual(self.store.card["current_balance"], 74.50)
        self.assertEqual(len(self.store.card_transactions), 1)
        self.assertEqual(self.store.card_transactions[0]["merchant_name"], "Demo Shop")
        self.assertEqual(self.store.payments[1]["status"], "completed")

    def test_frozen_card_charge_fails(self):
        self.store.card["is_frozen"] = True

        response = self.client.post(
            "/api/v1/payments/charge",
            headers={"X-Merchant-Api-Key": "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"},
            json={
                "amount": 10,
                "currency": "USD",
                "card_number": "4111111111111111",
                "cvv": "123",
                "expiry_date": "12/28",
                "merchant_order_id": "ORDER-FROZEN",
            },
        )

        body = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body["failure_reason"], "card_frozen")
        self.assertEqual(self.store.card["current_balance"], 100.0)
        self.assertEqual(self.store.payments[1]["status"], "failed")

    def test_insufficient_card_balance_fails(self):
        response = self.client.post(
            "/api/v1/payments/charge",
            headers={"X-Merchant-Api-Key": "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"},
            json={
                "amount": 150,
                "currency": "USD",
                "card_number": "4111111111111111",
                "cvv": "123",
                "expiry_date": "12/28",
                "merchant_order_id": "ORDER-LOW-BALANCE",
            },
        )

        body = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body["failure_reason"], "insufficient_card_balance")
        self.assertEqual(self.store.card["current_balance"], 100.0)
        self.assertEqual(self.store.payments[1]["status"], "failed")

    def test_payment_lookup_works_with_api_key_and_jwt(self):
        self._create_successful_payment()

        login_response = self.client.post(
            "/api/v1/merchants/login",
            json={"email": "shop@example.com", "password": "password123"},
        )
        token = login_response.get_json()["token"]

        api_key_response = self.client.get(
            "/api/v1/payments/1",
            headers={"X-Merchant-Api-Key": "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"},
        )
        jwt_response = self.client.get(
            "/api/v1/payments/1",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(api_key_response.status_code, 200)
        self.assertEqual(jwt_response.status_code, 200)
        self.assertEqual(api_key_response.get_json()["payment"]["id"], 1)
        self.assertEqual(jwt_response.get_json()["payment"]["id"], 1)

    def test_payment_list_returns_only_current_merchants_payments(self):
        self._create_successful_payment()
        self.store.payments[2] = {
            "id": 2,
            "merchant_id": 2,
            "merchant_name": "Other Shop",
            "card_id": 10,
            "amount": 12.0,
            "currency": "USD",
            "status": "completed",
            "merchant_order_id": "OTHER-ORDER",
            "authorization_code": "AUTHOTHER",
            "failure_reason": None,
            "created_at": self.store.created_at,
        }

        response = self.client.get(
            "/api/v1/payments",
            headers={"X-Merchant-Api-Key": "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"},
        )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual({payment["merchant_id"] for payment in body["payments"]}, {1})
        self.assertNotIn("bola_note", body["debug_info"])

    def test_payment_merchant_id_lookup_can_return_another_merchants_payments(self):
        self._create_successful_payment()
        self.store.payments[2] = {
            "id": 2,
            "merchant_id": 2,
            "merchant_name": "Other Shop",
            "card_id": 10,
            "amount": 12.0,
            "currency": "USD",
            "status": "completed",
            "merchant_order_id": "OTHER-ORDER",
            "authorization_code": "AUTHOTHER",
            "failure_reason": None,
            "created_at": self.store.created_at,
        }

        response = self.client.get(
            "/api/v1/payments/merchant_id/2",
            headers={"X-Merchant-Api-Key": "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"},
        )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual({payment["merchant_id"] for payment in body["payments"]}, {2})
        self.assertNotIn("bola_note", body["debug_info"])

    def _create_successful_payment(self):
        response = self.client.post(
            "/api/v1/payments/charge",
            headers={"X-Merchant-Api-Key": "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"},
            json={
                "amount": 10,
                "currency": "USD",
                "card_number": "4111111111111111",
                "cvv": "123",
                "expiry_date": "12/28",
                "merchant_order_id": "ORDER-LOOKUP",
            },
        )
        self.assertEqual(response.status_code, 200, msg=response.get_json())


class FakeMerchantStore:
    def __init__(self):
        self.created_at = datetime(2026, 5, 3, 12, 0, 0)
        self.merchant = {
            "id": 1,
            "name": "Demo Shop",
            "email": "shop@example.com",
            "password": "password123",
            "api_key": "vk_03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4",
            "is_active": True,
            "created_at": self.created_at,
        }
        self.card = {
            "id": 10,
            "user_id": 20,
            "card_number": "4111111111111111",
            "cvv": "123",
            "expiry_date": "12/28",
            "current_balance": 100.0,
            "is_frozen": False,
            "is_active": True,
            "currency": "USD",
            "card_type": "standard",
            "card_limit": 1000.0,
            "account_number": "1234567890",
            "username": "alice",
        }
        self.payments = {}
        self.card_transactions = []
        self.next_payment_id = 1

    def execute_query(self, query, params=None, fetch=True):
        normalized_query = " ".join(query.split())

        if "INSERT INTO merchants" in normalized_query:
            return [self._merchant_tuple()]

        if "FROM merchants" in normalized_query and "WHERE api_key" in normalized_query:
            return [self._merchant_tuple()]

        if "FROM merchants" in normalized_query and "WHERE email" in normalized_query:
            if "shop@example.com" in normalized_query and "password123" in normalized_query:
                return [self._merchant_tuple()]
            return []

        if "FROM merchants" in normalized_query and "WHERE id" in normalized_query:
            return [self._merchant_tuple()]

        if "FROM virtual_cards vc JOIN users u" in normalized_query:
            if self.card["card_number"] in normalized_query:
                return [self._card_tuple()]
            return []

        if normalized_query.startswith("UPDATE virtual_cards"):
            amount, card_id = params
            if card_id == self.card["id"]:
                self.card["current_balance"] -= float(amount)
            return None

        if "INSERT INTO card_transactions" in normalized_query:
            self.card_transactions.append(
                {
                    "card_id": params[0],
                    "amount": float(params[1]),
                    "merchant_name": params[2],
                    "transaction_type": params[3],
                    "status": params[4],
                    "description": params[5],
                }
            )
            return None

        if "INSERT INTO merchant_payments" in normalized_query:
            payment_id = self.next_payment_id
            self.next_payment_id += 1
            self.payments[payment_id] = {
                "id": payment_id,
                "merchant_id": params[0],
                "merchant_name": self.merchant["name"],
                "card_id": params[1],
                "amount": float(params[2]),
                "currency": params[3],
                "status": params[4],
                "merchant_order_id": params[5],
                "authorization_code": params[6],
                "failure_reason": params[7],
                "created_at": self.created_at,
            }
            return [(payment_id,)]

        if "FROM merchant_payments mp JOIN merchants m" in normalized_query and "WHERE mp.id" in normalized_query:
            payment_id = int(normalized_query.split("WHERE mp.id = ")[1].split()[0])
            payment = self.payments.get(payment_id)
            if not payment:
                return []
            if "AND mp.merchant_id =" in normalized_query:
                merchant_id = int(normalized_query.split("AND mp.merchant_id = ")[1].split()[0])
                if payment["merchant_id"] != merchant_id:
                    return []
            return [self._payment_detail_tuple(payment)]

        if "FROM merchant_payments mp JOIN merchants m" in normalized_query and "WHERE mp.merchant_id" in normalized_query:
            merchant_id = int(normalized_query.split("WHERE mp.merchant_id = ")[1].split()[0])
            return [
                self._payment_list_tuple(payment)
                for payment in self.payments.values()
                if payment["merchant_id"] == merchant_id
            ]

        if "FROM merchant_payments mp JOIN merchants m" in normalized_query:
            return [self._payment_list_tuple(payment) for payment in self.payments.values()]

        raise AssertionError(f"Unhandled query: {query}")

    def _merchant_tuple(self):
        return (
            self.merchant["id"],
            self.merchant["name"],
            self.merchant["email"],
            self.merchant["api_key"],
            self.merchant["is_active"],
            self.merchant["created_at"],
        )

    def _card_tuple(self):
        return (
            self.card["id"],
            self.card["user_id"],
            self.card["card_number"],
            self.card["cvv"],
            self.card["expiry_date"],
            self.card["current_balance"],
            self.card["is_frozen"],
            self.card["is_active"],
            self.card["currency"],
            self.card["card_type"],
            self.card["card_limit"],
            self.card["account_number"],
            self.card["username"],
        )

    def _payment_detail_tuple(self, payment):
        return (
            payment["id"],
            payment["merchant_id"],
            payment["merchant_name"],
            self.merchant["email"],
            payment["card_id"],
            self.card["card_number"] if payment["card_id"] else None,
            self.card["cvv"] if payment["card_id"] else None,
            payment["amount"],
            payment["currency"],
            payment["status"],
            payment["merchant_order_id"],
            payment["authorization_code"],
            payment["failure_reason"],
            payment["created_at"],
        )

    def _payment_list_tuple(self, payment):
        return (
            payment["id"],
            payment["merchant_id"],
            payment["merchant_name"],
            payment["card_id"],
            self.card["card_number"] if payment["card_id"] else None,
            payment["amount"],
            payment["currency"],
            payment["status"],
            payment["merchant_order_id"],
            payment["authorization_code"],
            payment["failure_reason"],
            payment["created_at"],
        )


if __name__ == "__main__":
    unittest.main()
