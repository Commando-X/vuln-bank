from unittest.mock import MagicMock
from verifiers.registry import VERIFIER_REGISTRY, register_verifiers


class TestVerifierRegistry:
    def test_registry_contains_all_22_verifiers(self):
        expected = {
            "sqli-login", "sqli-transfer", "sqli-graphql", "sqli-bills",
            "xss-bio-stored", "ssrf-profile-url", "ssrf-metadata",
            "bola-transactions", "bola-balance", "bola-cards", "bola-bills",
            "auth-jwt-none", "auth-jwt-weak-secret", "auth-mass-assignment", "auth-weak-reset",
            "ai-prompt-extraction", "ai-capability-extraction",
            "graphql-introspection", "page-coverage",
            "file-upload-path-traversal", "file-upload-unrestricted",
            "race-condition-transfer",
        }
        assert set(VERIFIER_REGISTRY.keys()) == expected

    def test_register_verifiers_only_registers_configured(self):
        wrapper = MagicMock()
        config = {"verifiers": ["sqli-login", "page-coverage"]}
        registered = register_verifiers(wrapper, config)
        assert set(registered) == {"sqli-login", "page-coverage"}

    def test_register_verifiers_empty_list(self):
        wrapper = MagicMock()
        config = {"verifiers": []}
        registered = register_verifiers(wrapper, config)
        assert registered == []

    def test_register_verifiers_ignores_unknown(self):
        wrapper = MagicMock()
        config = {"verifiers": ["nonexistent-verifier"]}
        registered = register_verifiers(wrapper, config)
        assert registered == []
