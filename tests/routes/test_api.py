import falcon
import pytest
import falcon.testing
import sqlalchemy.ext.asyncio


def test_auth_endpoint(client: falcon.testing.TestClient):
    resp = client.simulate_get("/auth")
    assert resp.status_code == 400
    resp = client.simulate_get(
        "/auth",
        content_type="application/json",
        json={"username": "test_user", "role": "brand"},
    )
    assert resp.status_code == 200


def test_discounts_endpoint(client: falcon.testing.TestClient, auth_brand: str):
    resp = client.simulate_get(
        "/discounts", headers={"Authorization": "Bearer " + auth_brand}
    )
    assert resp.status_code == 200
    assert "availableDiscounts" in resp.json


def test_create_discounts_endpoint(client: falcon.testing.TestClient, auth_brand: str):
    resp = client.simulate_post(
        "/discount/create",
        content_type="application/json",
        json={"name": "Test Discount", "percentage": 80, "nCodes": 2000},
        headers={"Authorization": "Bearer " + auth_brand},
    )
    assert resp.status_code == 201
    assert resp.json["name"] == "Test Discount"
    resp = client.simulate_get(
        "/discounts", headers={"Authorization": "Bearer " + auth_brand}
    )
    assert any(
        discount["name"] == "Test Discount"
        for discount in resp.json["availableDiscounts"]
    )


def test_claim_discount_endpoint(
    client: falcon.testing.TestClient, auth_user: str, auth_brand: str
):
    resp = client.simulate_post(
        "/discount/create",
        content_type="application/json",
        json={"name": "Test Discount", "percentage": 80, "nCodes": 2000},
        headers={"Authorization": "Bearer " + auth_brand},
    )
    code_id = str(resp.json["id"])
    resp = client.simulate_post(
        "/discount/" + code_id + "/claim",
        content_type="application/json",
        headers={"Authorization": "Bearer " + auth_user},
    )
    assert resp.status_code == 200
    resp = client.simulate_post(
        "/discount/" + code_id + "/claim",
        content_type="application/json",
        headers={"Authorization": "Bearer " + auth_user},
    )
    assert resp.status_code == 409
