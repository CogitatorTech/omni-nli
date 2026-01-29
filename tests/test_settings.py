"""Tests for settings module."""

from omni_nli.settings import ServerSettings


class TestServerSettings:
    """Tests for ServerSettings configuration."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = ServerSettings()

        assert settings.host == "127.0.0.1"
        assert settings.port == 8000
        assert settings.log_level == "INFO"
        assert settings.debug is False
        assert settings.default_backend == "huggingface"
        assert settings.max_thinking_tokens == 4096
        assert settings.return_thinking_trace is False
        assert settings.provider_cache_size == 8

    def test_custom_values(self):
        """Test that custom values can be set."""
        settings = ServerSettings(
            host="0.0.0.0",
            port=9000,
            log_level="DEBUG",
            debug=True,
            default_backend="ollama",
        )

        assert settings.host == "0.0.0.0"
        assert settings.port == 9000
        assert settings.log_level == "DEBUG"
        assert settings.debug is True
        assert settings.default_backend == "ollama"

    def test_ollama_settings(self):
        """Test Ollama-specific settings."""
        settings = ServerSettings(
            ollama_host="http://custom-host:11434",
            ollama_default_model="phi4:latest",
        )

        assert settings.ollama_host == "http://custom-host:11434"
        assert settings.ollama_default_model == "phi4:latest"

    def test_huggingface_settings(self):
        """Test HuggingFace-specific settings."""
        settings = ServerSettings(
            huggingface_token="hf_test_token",
            huggingface_default_model="Qwen/Qwen2.5-1.5B-Instruct",
            hf_cache_dir="/tmp/hf_cache",
        )

        assert settings.huggingface_token == "hf_test_token"
        assert settings.huggingface_default_model == "Qwen/Qwen2.5-1.5B-Instruct"
        assert settings.hf_cache_dir == "/tmp/hf_cache"

    def test_openrouter_settings(self):
        """Test OpenRouter-specific settings."""
        settings = ServerSettings(
            openrouter_api_key="sk-or-test-key",
            openrouter_default_model="openai/gpt-5.2",
        )

        assert settings.openrouter_api_key == "sk-or-test-key"
        assert settings.openrouter_default_model == "openai/gpt-5.2"

    def test_pkg_version_exists(self):
        """Test that package version is available."""
        settings = ServerSettings()
        assert settings.pkg_version is not None
        assert isinstance(settings.pkg_version, str)

    def test_settings_are_mutable(self):
        """Test that settings can be modified after creation."""
        settings = ServerSettings()

        settings.host = "192.168.1.1"
        settings.port = 3000
        settings.debug = True

        assert settings.host == "192.168.1.1"
        assert settings.port == 3000
        assert settings.debug is True
