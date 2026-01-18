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

    def test_load_user_instructions_no_file(self):
        """When prompt.md doesn't exist, returns None."""
        import config
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
            temp_path = Path(f.name)
        try:
            with patch.object(config, "PROMPT_FILE", temp_path):
                temp_path.unlink()  # Ensure doesn't exist
                result = config.load_user_instructions()
                assert result is None
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_load_user_instructions_with_file(self):
        """When prompt.md exists, returns its contents."""
        import config
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode="w") as f:
            f.write("Custom instructions here")
            temp_path = Path(f.name)
        try:
            with patch.object(config, "PROMPT_FILE", temp_path):
                result = config.load_user_instructions()
                assert result == "Custom instructions here"
        finally:
            temp_path.unlink()


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

    def test_pydantic_models_valid(self):
        """Test that PilotResponse and TmuxCommand models work correctly."""
        import gemini

        # Test TmuxCommand
        cmd = gemini.TmuxCommand(target="main:0", keys="ls -la")
        assert cmd.target == "main:0"
        assert cmd.keys == "ls -la"

        # Test TmuxCommand with defaults
        cmd_default = gemini.TmuxCommand()
        assert cmd_default.target == ""
        assert cmd_default.keys == ""

        # Test PilotResponse
        response = gemini.PilotResponse(
            commands=[gemini.TmuxCommand(target="main:0", keys="ls")],
            display="Status display",
            task="current task",
            note="log entry"
        )
        assert len(response.commands) == 1
        assert response.display == "Status display"
        assert response.task == "current task"
        assert response.note == "log entry"

        # Test PilotResponse with minimal required fields
        response_minimal = gemini.PilotResponse(display="Just display")
        assert response_minimal.commands == []
        assert response_minimal.task is None
        assert response_minimal.note is None

    def test_pydantic_model_json_parsing(self):
        """Test that PilotResponse can parse JSON correctly."""
        import gemini

        json_str = json.dumps({
            "commands": [{"target": "main:0", "keys": "ls"}],
            "display": "Listing files",
            "task": "file listing",
            "note": "ran ls"
        })

        response = gemini.PilotResponse.model_validate_json(json_str)
        assert response.display == "Listing files"
        assert len(response.commands) == 1
        assert response.commands[0].target == "main:0"
        assert response.commands[0].keys == "ls"

        # Test model_dump returns dict
        result_dict = response.model_dump()
        assert isinstance(result_dict, dict)
        assert result_dict["display"] == "Listing files"
        assert result_dict["commands"][0]["keys"] == "ls"

    def test_get_system_prompt_default(self):
        """Test get_system_prompt uses default when no custom file."""
        import gemini
        with patch.object(gemini, "load_user_instructions", return_value=None):
            prompt = gemini.get_system_prompt()
            assert gemini.CORE_SCHEMA_INSTRUCTION in prompt
            assert gemini.DEFAULT_USER_INSTRUCTIONS in prompt

    def test_get_system_prompt_custom(self):
        """Test get_system_prompt uses custom instructions when available."""
        import gemini
        custom = "My custom instructions"
        with patch.object(gemini, "load_user_instructions", return_value=custom):
            prompt = gemini.get_system_prompt()
            assert gemini.CORE_SCHEMA_INSTRUCTION in prompt
            assert custom in prompt
            assert gemini.DEFAULT_USER_INSTRUCTIONS not in prompt

    @pytest.mark.asyncio
    async def test_translate_no_api_key(self):
        import gemini
        with patch.object(gemini, "client", None):
            result = await gemini.translate(text="hello")
            assert "Error" in result["display"]
            assert result["commands"] == []

    @pytest.mark.asyncio
    async def test_translate_success(self):
        """Test successful translation with structured output."""
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
            assert result["commands"][0]["target"] == "main:0"
            assert result["task"] == "file listing"
            assert result["note"] == "ran ls"

    @pytest.mark.asyncio
    async def test_translate_structured_output_config(self):
        """Test that translate() uses response_schema in config."""
        import gemini
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "commands": [],
            "display": "Status",
            "task": None,
            "note": None
        })

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch.object(gemini, "client", mock_client):
            await gemini.translate(text="status")

            # Verify generate_content was called with correct config
            call_args = mock_client.aio.models.generate_content.call_args
            config = call_args.kwargs.get("config") or call_args[1].get("config")
            assert config.response_mime_type == "application/json"
            assert config.response_schema == gemini.PilotResponse

    @pytest.mark.asyncio
    async def test_translate_pydantic_validation_error(self):
        """Test that validation errors are handled gracefully."""
        import gemini
        mock_response = MagicMock()
        mock_response.text = "not valid json"

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch.object(gemini, "client", mock_client):
            result = await gemini.translate(text="hello")
            # Should return error response, not crash
            assert "commands" in result
            assert result["commands"] == []
            assert "note" in result


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
