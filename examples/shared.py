import argparse


def get_args(default_url: str) -> argparse.Namespace:
    """Parses and returns command-line arguments for the examples."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--premise",
        type=str,
        default="A soccer player is sprinting across the field.",
        help="The premise text.",
    )
    parser.add_argument(
        "--hypothesis",
        type=str,
        default="A person is sitting down.",
        help="The hypothesis text.",
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="ollama",
        help="The backend to use (ollama, huggingface, openrouter).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Specific model to use.",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=default_url,
        help="The URL for the endpoint.",
    )
    return parser.parse_args()
