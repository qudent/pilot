"""Tests for pilot server."""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import os

# Set test environment before imports
os.environ["GEMINI_API_KEY"] = "test-key"


class TestConfig:
    """Test config module."""

    def test_pilot_home_created(self):
        import config
        assert config.PILOT_HOME.exists()

    def test_token_exists(self):
        import config
        assert config.AUTH_TOKEN
        assert len(config.AUTH_TOKEN) > 20


class TestTmux:
    """Test tmux module."""

    def test_run_command(self):
        import tmux
        result = tmux.run("echo hello")
        assert "hello" in result

    @patch("tmux.run")
    def test_list_sessions_empty(self, mock_run):
        import tmux
        mock_run.return_value = "no server running"
        sessions = tmux.list_sessions()
        assert sessions == []

    @patch("tmux.run")
    def test_list_sessions_has_sessions(self, mock_run):
        import tmux
        mock_run.return_value = "main\nwork\n"
        sessions = tmux.list_sessions()
        assert sessions == ["main", "work"]

    @patch("tmux.run")
    def test_send_keys(self, mock_run):
        import tmux
        mock_run.return_value = ""
        result = tmux.send_keys("ls -la", session="main")
        assert mock_run.called
        call_arg = mock_run.call_args[0][0]
        assert "-t main" in call_arg
        assert "ls -la" in call_arg


class TestContext:
    """Test context module."""

    def test_load_empty(self):
        import context
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
            temp_path = Path(f.name)
        try:
            with patch.object(context, "CONTEXT_FILE", temp_path):
                temp_path.unlink()  # Ensure doesn't exist
                result = context.load()
                assert result == ""
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_save_and_load(self):
        import context
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
            temp_path = Path(f.name)
        try:
            with patch.object(context, "CONTEXT_FILE", temp_path):
                context.save("test content")
                result = context.load()
                assert result == "test content"
        finally:
            temp_path.unlink()

    def test_save_truncates_long_content(self):
        import context
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
            temp_path = Path(f.name)
        try:
            with patch.object(context, "CONTEXT_FILE", temp_path):
                with patch.object(context, "CONTEXT_MAX_LINES", 20):
                    long_content = "\n".join([f"line {i}" for i in range(100)])
                    context.save(long_content)
                    result = context.load()
                    lines = result.split("\n")
                    assert len(lines) <= 25  # Some slack for truncation marker


        finally:
            temp_path.unlink()


class TestGemini:
    """Test gemini module."""

    @pytest.mark.asyncio
    async def test_translate_no_api_key(self):
        import gemini
        with patch.object(gemini, "client", None):
            result = await gemini.translate(text="hello")
            assert "Error" in result["display"]
            assert result["commands"] == []

    @pytest.mark.asyncio
    async def test_translate_success(self):
        import gemini
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "commands": [{"target": "main:0", "keys": "ls"}],
            "display": "Listing files",
            "task": "file listing",
            "note": "ran ls"
        })

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch.object(gemini, "client", mock_client):
            result = await gemini.translate(
                text="list files",
                screen={"cols": 80, "rows": 24},
            )
            assert result["display"] == "Listing files"
            assert len(result["commands"]) == 1
            assert result["commands"][0]["keys"] == "ls"

    @pytest.mark.asyncio
    async def test_translate_json_parse_error(self):
        import gemini
        mock_response = MagicMock()
        mock_response.text = "not valid json"

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch.object(gemini, "client", mock_client):
            result = await gemini.translate(text="hello")
            assert "note" in result
            assert "parse" in result["note"].lower() or result["display"]


class TestServer:
    """Test server endpoints."""

    def test_index_returns_html(self):
        from fastapi.testclient import TestClient
        import server
        client = TestClient(server.app)
        response = client.get("/")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()

    def test_verify_token(self):
        import server
        import config
        assert server.verify_token(config.AUTH_TOKEN) is True
        assert server.verify_token("wrong-token") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
