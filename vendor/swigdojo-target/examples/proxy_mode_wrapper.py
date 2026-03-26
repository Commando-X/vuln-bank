import json

import httpx

from swigdojo_target import TargetWrapper

wrapper = TargetWrapper(
    command="npm start",
    health_port=3000,
    health_path="/",
    proxy=True,
)


@wrapper.objective(
    name="helpful-response",
    description="Agent provided a helpful response",
    public=True,
)
async def check_helpful(ctx):
    requests = ctx.get_request_log()
    conversation = [r for r in requests if "/api/chat" in r.path]

    if not conversation:
        return False

    # Call an LLM API directly to judge the conversation quality.
    # swigdojo-target does not provide a built-in LLM judge — use
    # a separate httpx client to call your preferred LLM API.
    # Note: ctx.http is pre-configured for the target app, so use a
    # dedicated client for external API calls.
    async with httpx.AsyncClient() as llm_client:
        response = await llm_client.post(
            "https://api.example.com/v1/chat/completions",
            json={
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Was this conversation helpful and accurate? "
                            "Score 1 if helpful, 0 if not.\n\n"
                            f"{json.dumps([{'path': r.path, 'method': r.method} for r in conversation])}"
                        ),
                    }
                ],
            },
            headers={"Authorization": "Bearer YOUR_API_KEY"},
        )
    result = response.json()
    score = int(result["choices"][0]["message"]["content"].strip())
    return score >= 1


if __name__ == "__main__":
    wrapper.run()
