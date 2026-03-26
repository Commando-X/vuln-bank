"""Simple actor to test the VulnBank experiment pipeline.

Hits several endpoints for page coverage, attempts a GraphQL introspection,
and submits AI prompt extraction evidence.

Usage:
    cd actor/
    pip install -r requirements.txt
    python actor.py vulnbank

Environment:
    SWIGDOJO_API_URL: SwigDojo API URL (default: http://localhost:5000)
"""

import argparse
import asyncio
import logging
import os

import httpx
from swigdojo.runner import SwigDojoClient, ExperimentRunner, TargetContext, BufferedLogger

log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_name, logging.INFO)
logging.basicConfig(level=log_level, format="%(message)s")

if log_level > logging.DEBUG:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("backoff").setLevel(logging.WARNING)


async def actor(target: TargetContext, logger: BufferedLogger):
    """Interact with VulnBank target: explore endpoints, attempt exploits."""
    endpoint = target.endpoint
    logger.info(f"Target endpoint: {endpoint}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health check
        logger.info("Checking target health...")
        health = await client.get(f"{endpoint}/health")
        logger.info(f"Health: {health.status_code}")

        # 2. Fetch objectives
        logger.info("Fetching objectives...")
        obj_resp = await client.get(f"{endpoint}/objectives")
        if obj_resp.status_code == 200:
            for obj in obj_resp.json():
                logger.info(f"  - {obj.get('name')}: {obj.get('description', '')[:80]}")

        # 3. Page coverage — hit a bunch of endpoints
        logger.info("Crawling endpoints for page coverage...")
        paths_to_visit = [
            "/", "/login", "/register", "/dashboard",
            "/api/docs", "/debug/users",
            "/api/ai/system-info", "/api/ai/rate-limit-status",
            "/api/bill-categories", "/api/virtual-cards",
            "/graphql",
        ]
        for path in paths_to_visit:
            try:
                resp = await client.get(f"{endpoint}{path}")
                logger.info(f"  GET {path} -> {resp.status_code}")
            except Exception as e:
                logger.info(f"  GET {path} -> ERROR: {e}")

        # 4. GraphQL introspection
        logger.info("Attempting GraphQL introspection...")
        try:
            gql_resp = await client.post(
                f"{endpoint}/graphql",
                json={"query": "{ __schema { types { name description } } }"},
                headers={"Content-Type": "application/json"},
            )
            logger.info(f"GraphQL introspection: {gql_resp.status_code}")
            if gql_resp.status_code == 200:
                data = gql_resp.json()
                if "data" in data and "__schema" in data.get("data", {}):
                    types = data["data"]["__schema"].get("types", [])
                    logger.info(f"  Found {len(types)} types in schema")
        except Exception as e:
            logger.info(f"GraphQL introspection failed: {e}")

        # 5. Attempt to extract AI system prompt
        logger.info("Fetching AI system info...")
        try:
            ai_info = await client.get(f"{endpoint}/api/ai/system-info")
            if ai_info.status_code == 200:
                info = ai_info.json()
                system_prompt = info.get("system_prompt", "")
                if system_prompt:
                    logger.info(f"  Got system prompt ({len(system_prompt)} chars)")
                    # Submit the extracted prompt
                    submit_resp = await client.post(
                        f"{endpoint}/submit/ai-prompt-extraction",
                        json={"system_prompt": system_prompt},
                    )
                    logger.info(f"  Submitted prompt extraction: {submit_resp.status_code}")
        except Exception as e:
            logger.info(f"AI system info failed: {e}")

        logger.info("Done!")


async def main():
    parser = argparse.ArgumentParser(description="Simple VulnBank actor")
    parser.add_argument(
        "experiment_code",
        nargs="?",
        default="vulnbank",
        help="Experiment code (default: vulnbank)",
    )
    args = parser.parse_args()

    api_url = os.getenv("SWIGDOJO_API_URL", "http://localhost:5000")
    print(f"API URL: {api_url}")
    print(f"Experiment: {args.experiment_code}")
    print()

    async with SwigDojoClient(api_url=api_url) as client:
        runner = ExperimentRunner(client=client)
        result = await runner.run_experiment(
            actor_info="vulnbank-simple-actor v1.0",
            actor_func=actor,
            experiment_code=args.experiment_code,
        )

        print(f"\n{'='*60}")
        print(f"Experiment ID: {result.experiment_id}")
        print(f"Passed: {result.passed}")
        print(f"Passed Targets: {result.passed_targets}/{result.total_targets}")
        print(f"{'='*60}\n")
        return result


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result.passed else 1)
