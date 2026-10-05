"""
Integration tests through the actual API. These check PROPERTIES that
must hold regardless of whether the real trained model or the fallback
heuristic is active on whatever machine runs this suite (both paths
respect breed differentiation and recent-history influence, by design).
"""


def register_and_login(client, email, password="CorrectPass123"):
    client.post("/auth/register", json={
        "first_name": "Test", "last_name": "Farmer", "email": email, "password": password,
    })
    tokens = client.post("/auth/login", data={"username": email, "password": password}).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def create_cow(client, headers, name, breed):
    return client.post("/api/cows", json={"name": name, "breed": breed}, headers=headers).json()


class TestLogCreationIncludesMLFields:
    def test_response_has_predicted_yield_and_model_flag(self, client):
        headers = register_and_login(client, "mltest1@example.com")
        cow = create_cow(client, headers, "Bessie", "holstein_friesian")

        resp = client.post("/api/logs", json={
            "cow_id": cow["id"], "date": "2026-01-01", "feed": 12,
            "milkingTimes": 2, "milkings": [8, 7],
        }, headers=headers)

        assert resp.status_code == 201
        body = resp.json()
        assert "predicted_yield" in body
        assert isinstance(body["predicted_yield"], float)
        assert "used_ml_model" in body
        assert isinstance(body["used_ml_model"], bool)


class TestBreedAffectsPrediction:
    def test_holstein_friesian_predicted_higher_than_ankole(self, client):
        """Core biological fact from Manzi et al. -- must hold for a
        brand-new cow of each breed, with identical feed/milking inputs
        and no log history to otherwise explain a difference."""
        headers = register_and_login(client, "mltest2@example.com")
        hf_cow = create_cow(client, headers, "Holsteina", "holstein_friesian")
        ankole_cow = create_cow(client, headers, "Ankolea", "ankole")

        hf_pred = client.post("/api/logs/predict", json={
            "cow_id": hf_cow["id"], "feed": 12, "milking_times": 2,
        }, headers=headers).json()["expected_yield"]

        ankole_pred = client.post("/api/logs/predict", json={
            "cow_id": ankole_cow["id"], "feed": 12, "milking_times": 2,
        }, headers=headers).json()["expected_yield"]

        assert hf_pred > ankole_pred


class TestRecentHistoryInfluencesPrediction:
    def test_established_high_yield_history_raises_prediction(self, client):
        """A cow with a consistently high recent yield history should get
        a noticeably higher prediction than a brand-new cow of the same
        breed with no history at all."""
        headers = register_and_login(client, "mltest3@example.com")

        fresh_cow = create_cow(client, headers, "Fresh", "other")
        established_cow = create_cow(client, headers, "Established", "other")

        # Give the established cow a week of consistently high yield
        for day in range(1, 8):
            client.post("/api/logs", json={
                "cow_id": established_cow["id"], "date": f"2026-01-0{day}",
                "feed": 12, "milkingTimes": 2, "milkings": [15, 14],
            }, headers=headers)

        fresh_pred = client.post("/api/logs/predict", json={
            "cow_id": fresh_cow["id"], "feed": 12, "milking_times": 2,
        }, headers=headers).json()["expected_yield"]

        established_pred = client.post("/api/logs/predict", json={
            "cow_id": established_cow["id"], "feed": 12, "milking_times": 2,
        }, headers=headers).json()["expected_yield"]

        assert established_pred > fresh_pred


class TestPredictionRespectsOwnership:
    def test_farmer_cannot_predict_for_unowned_cow(self, client):
        headers_a = register_and_login(client, "mltest4a@example.com")
        headers_b = register_and_login(client, "mltest4b@example.com")

        cow = create_cow(client, headers_a, "NotYours", "ankole")

        resp = client.post("/api/logs/predict", json={
            "cow_id": cow["id"], "feed": 10, "milking_times": 2,
        }, headers=headers_b)

        assert resp.status_code == 404