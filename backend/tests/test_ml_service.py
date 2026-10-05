"""
Unit tests for MLService's deterministic behavior: the fallback heuristic,
the Rwanda-calibrated breed priors, and the model integrity check.
They force the fallback path explicitly, so they don't depend on whether
the real .pkl exists on the machine running them.
"""
from app.services.ml_service import MLService, BREED_PRIOR_YIELD_L


def make_fallback_service() -> MLService:
    return MLService(model_path="/nonexistent/path/model.pkl")


class TestFallbackHeuristic:
    def test_not_loaded_when_file_missing(self):
        assert make_fallback_service().is_loaded is False

    def test_uses_recent_avg_yield_directly_when_provided(self):
        result = make_fallback_service().predict_expected_yield(
            feed=10, milking_times=2, breed="holstein_friesian", recent_avg_yield=15.3
        )
        assert result == 15.3

    def test_uses_breed_prior_when_no_history(self):
        service = make_fallback_service()
        for breed, expected_prior in BREED_PRIOR_YIELD_L.items():
            result = service.predict_expected_yield(
                feed=10, milking_times=2, breed=breed, recent_avg_yield=None
            )
            assert result == expected_prior

    def test_unknown_breed_defaults_to_other_prior(self):
        result = make_fallback_service().predict_expected_yield(
            feed=10, milking_times=2, breed="some_breed_not_in_our_enum", recent_avg_yield=None
        )
        assert result == BREED_PRIOR_YIELD_L["other"]


class TestRwandaCalibratedPriors:
    def test_holstein_friesian_prior_matches_research(self):
        assert BREED_PRIOR_YIELD_L["holstein_friesian"] == 13.0

    def test_ankole_prior_matches_research(self):
        assert BREED_PRIOR_YIELD_L["ankole"] == 2.5

    def test_ankole_friesian_cross_prior_matches_research(self):
        assert BREED_PRIOR_YIELD_L["ankole_friesian_cross"] == 7.0

    def test_holstein_friesian_exceeds_ankole(self):
        assert BREED_PRIOR_YIELD_L["holstein_friesian"] > BREED_PRIOR_YIELD_L["ankole"]


class TestModelIntegrityCheck:
    def test_wrong_hash_falls_back_gracefully(self, tmp_path, monkeypatch):
        fake_model_path = tmp_path / "fake_model.pkl"
        fake_model_path.write_bytes(b"not a real model")

        monkeypatch.setattr("app.services.ml_service.settings.ml_model_sha256", "0" * 64)
        service = MLService(model_path=str(fake_model_path))

        assert service.is_loaded is False  # refused to load a file whose hash doesn't match
        result = service.predict_expected_yield(
            feed=10, milking_times=2, breed="ankole", recent_avg_yield=None
        )
        assert result == BREED_PRIOR_YIELD_L["ankole"]
