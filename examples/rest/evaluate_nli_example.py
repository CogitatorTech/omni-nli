import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

import httpx
from shared import get_args


def main() -> None:
    """Sends an NLI request to the REST API and prints the result."""
    args = get_args(default_url="http://127.0.0.1:8000/api/v1/nli/evaluate")

    payload = {
        "premise": args.premise,
        "hypothesis": args.hypothesis,
        "backend": args.backend,
        "use_reasoning": True,
    }

    if args.model:
        payload["model"] = args.model

    print(f"Sending request to {args.url}")
    print(f"backend: {args.backend}, model: {args.model}")
    print(f"premise: {args.premise}")
    print(f"hypothesis: {args.hypothesis}")

    try:
        response = httpx.post(args.url, json=payload, timeout=60)
        response.raise_for_status()

        print("\nResponse from server:")
        print(json.dumps(response.json(), indent=2))

    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}.")
        print(e)
    except httpx.HTTPStatusError as e:
        print(f"Error response {e.response.status_code} while requesting {e.request.url!r}.")
        print(f"Response body: {e.response.text}")


if __name__ == "__main__":
    main()
