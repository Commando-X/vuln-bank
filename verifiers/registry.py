from verifiers.sqli import register_sqli_login, register_sqli_transfer, register_sqli_graphql, register_sqli_bills
from verifiers.xss import register_xss_bio_stored
from verifiers.ssrf import register_ssrf_profile_url, register_ssrf_metadata
from verifiers.bola import register_bola_transactions, register_bola_balance, register_bola_cards, register_bola_bills
from verifiers.auth import register_auth_jwt_none, register_auth_jwt_weak_secret, register_auth_mass_assignment, register_auth_weak_reset
from verifiers.ai_extraction import register_ai_prompt_extraction, register_ai_capability_extraction
from verifiers.graphql import register_graphql_introspection
from verifiers.coverage import register_page_coverage
from verifiers.file_upload import register_file_upload_path_traversal, register_file_upload_unrestricted
from verifiers.race_condition import register_race_condition_transfer

VERIFIER_REGISTRY = {
    "sqli-login": register_sqli_login,
    "sqli-transfer": register_sqli_transfer,
    "sqli-graphql": register_sqli_graphql,
    "sqli-bills": register_sqli_bills,
    "xss-bio-stored": register_xss_bio_stored,
    "ssrf-profile-url": register_ssrf_profile_url,
    "ssrf-metadata": register_ssrf_metadata,
    "bola-transactions": register_bola_transactions,
    "bola-balance": register_bola_balance,
    "bola-cards": register_bola_cards,
    "bola-bills": register_bola_bills,
    "auth-jwt-none": register_auth_jwt_none,
    "auth-jwt-weak-secret": register_auth_jwt_weak_secret,
    "auth-mass-assignment": register_auth_mass_assignment,
    "auth-weak-reset": register_auth_weak_reset,
    "ai-prompt-extraction": register_ai_prompt_extraction,
    "ai-capability-extraction": register_ai_capability_extraction,
    "graphql-introspection": register_graphql_introspection,
    "page-coverage": register_page_coverage,
    "file-upload-path-traversal": register_file_upload_path_traversal,
    "file-upload-unrestricted": register_file_upload_unrestricted,
    "race-condition-transfer": register_race_condition_transfer,
}


def register_verifiers(wrapper, config: dict) -> list[str]:
    verifier_names = config.get("verifiers", [])
    registered = []
    for name in verifier_names:
        register_fn = VERIFIER_REGISTRY.get(name)
        if register_fn:
            register_fn(wrapper, config)
            registered.append(name)
    return registered
