import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import httpx


def main() -> None:
    """Lists available models for a given backend via the REST API."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:8000/api/v1/models",
        help="The base URL for the models endpoint (without query string).",
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="ollama",
        help="Backend to list models for (ollama, huggingface, openrouter).",
    )
    args = parser.parse_args()

    print(f"Requesting models from {args.url} for backend={args.backend}")

    try:
        response = httpx.get(args.url, params={"backend": args.backend}, timeout=60)
        response.raise_for_status()
        print("\nResponse from server:")
        print(response.json())

    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}.")
        print(e)
    except httpx.HTTPStatusError as e:
        print(f"Error response {e.response.status_code} while requesting {e.request.url!r}.")
        print(f"Response body: {e.response.text}")


if __name__ == "__main__":
    main()
