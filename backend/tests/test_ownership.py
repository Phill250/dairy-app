def register_and_login(client, email, password="CorrectPass123"):
    client.post("/auth/register", json={
        "first_name": "Test", "last_name": "User", "email": email, "password": password,
    })
    tokens = client.post("/auth/login", data={"username": email, "password": password}).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestFarmerOwnershipIsolation:
    def test_farmer_cannot_see_another_farmers_cow(self, client):
        headers_a = register_and_login(client, "farmerA@example.com")
        headers_b = register_and_login(client, "farmerB@example.com")

        cow_id = client.post(
            "/api/cows", json={"name": "Bessie", "breed": "holstein_friesian"}, headers=headers_a
        ).json()["id"]

        list_resp = client.get("/api/cows", headers=headers_b)
        assert list_resp.status_code == 200
        assert all(c["id"] != cow_id for c in list_resp.json())

    def test_farmer_cannot_create_log_on_another_farmers_cow(self, client):
        headers_a = register_and_login(client, "farmerC@example.com")
        headers_b = register_and_login(client, "farmerD@example.com")

        cow_id = client.post(
            "/api/cows", json={"name": "Nyota", "breed": "ankole"}, headers=headers_a
        ).json()["id"]

        resp = client.post("/api/logs", json={
            "cow_id": cow_id, "date": "2026-01-01", "feed": 10,
            "milkingTimes": 2, "milkings": [5, 5],
        }, headers=headers_b)
        assert resp.status_code == 404

    def test_farmer_cannot_read_another_farmers_log_by_guessing_id(self, client):
        headers_a = register_and_login(client, "farmerE@example.com")
        headers_b = register_and_login(client, "farmerF@example.com")

        cow_id = client.post(
            "/api/cows", json={"name": "Kaka", "breed": "other"}, headers=headers_a
        ).json()["id"]
        log_id = client.post("/api/logs", json={
            "cow_id": cow_id, "date": "2026-01-01", "feed": 10,
            "milkingTimes": 2, "milkings": [5, 5],
        }, headers=headers_a).json()["id"]

        resp = client.get(f"/api/logs/{log_id}", headers=headers_b)
        assert resp.status_code == 404


class TestAdminScopeIsEnforced:
    def test_farmer_cannot_access_admin_metrics(self, client):
        headers = register_and_login(client, "regularfarmer@example.com")
        resp = client.get("/api/admin/metrics", headers=headers)
        assert resp.status_code == 403

    def test_farmer_cannot_self_promote_to_admin(self, client):
        headers = register_and_login(client, "sneaky@example.com")
        resp = client.post("/auth/register-admin", json={
            "first_name": "Fake", "last_name": "Admin",
            "email": "fakeadmin@example.com", "password": "SomePass123",
        }, headers=headers)
        assert resp.status_code == 403
        
class TestCowAndLogDeletion:
    def test_farmer_cannot_update_another_farmers_cow(self, client):
        headers_a = register_and_login(client, "cowownerA@example.com")
        headers_b = register_and_login(client, "cowownerB@example.com")

        cow_id = client.post(
            "/api/cows", json={"name": "Original", "breed": "other"}, headers=headers_a
        ).json()["id"]

        resp = client.patch(f"/api/cows/{cow_id}", json={"name": "Hijacked"}, headers=headers_b)
        assert resp.status_code == 404

    def test_farmer_cannot_delete_another_farmers_cow(self, client):
        headers_a = register_and_login(client, "cowownerC@example.com")
        headers_b = register_and_login(client, "cowownerD@example.com")

        cow_id = client.post(
            "/api/cows", json={"name": "Safe", "breed": "other"}, headers=headers_a
        ).json()["id"]

        resp = client.delete(f"/api/cows/{cow_id}", headers=headers_b)
        assert resp.status_code == 404

    def test_owner_can_delete_own_log(self, client):
        headers = register_and_login(client, "logownerA@example.com")
        cow_id = client.post(
            "/api/cows", json={"name": "MyCow", "breed": "other"}, headers=headers
        ).json()["id"]
        log_id = client.post("/api/logs", json={
            "cow_id": cow_id, "date": "2026-01-01", "feed": 10,
            "milkingTimes": 2, "milkings": [5, 5],
        }, headers=headers).json()["id"]

        resp = client.delete(f"/api/logs/{log_id}", headers=headers)
        assert resp.status_code == 204

        resp = client.get(f"/api/logs/{log_id}", headers=headers)
        assert resp.status_code == 404
        
        
# add to backend/tests/test_ownership.py or a new test_trend.py
def create_cow(client, headers, name, breed):
    return client.post("/api/cows", json={"name": name, "breed": breed}, headers=headers).json()

def test_gradual_decline_flagged_even_when_today_looks_normal(client):
    headers = register_and_login(client, "trendtest@example.com")
    cow = create_cow(client, headers, "Slowfade", "other")

    # Simulate a steady week-long decline: 15, 14, 13, 12L...
    for day, yield_val in enumerate([15, 14, 13, 12], start=1):
        client.post("/api/logs", json={
            "cow_id": cow["id"], "date": f"2026-01-0{day}",
            "feed": 12, "milkingTimes": 2, "milkings": [yield_val / 2, yield_val / 2],
        }, headers=headers)

    # Today's yield is close to the (already-declined) recent average --
    # a naive single-day comparison would call this "Good Condition"
    resp = client.post("/api/logs", json={
        "cow_id": cow["id"], "date": "2026-01-05",
        "feed": 12, "milkingTimes": 2, "milkings": [5.5, 5.5],
    }, headers=headers)

    body = resp.json()
    assert "trending down" in body["advice"].lower() or body["status"] != "Good Condition"
    
    
# add to backend/tests/test_ownership.py

class TestAdminUserListStaysNonIdentifying:
    def test_response_has_no_name_or_email_fields(self, client):
        # Bootstrap requires an actual admin token, so this test only
        # verifies the SHAPE of the response schema is enforced --
        # AdminUserSummary simply has no name/email fields to leak,
        # regardless of who calls it.
        from app.schemas.admin import AdminUserSummary
        assert "email" not in AdminUserSummary.model_fields
        assert "first_name" not in AdminUserSummary.model_fields
        assert "last_name" not in AdminUserSummary.model_fields