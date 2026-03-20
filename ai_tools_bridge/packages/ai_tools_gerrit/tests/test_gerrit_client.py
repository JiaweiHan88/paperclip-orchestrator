"""Test cases for GerritClient."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from ai_tools_gerrit.gerrit_client import GerritApiError, GerritClient, encode_project_name

XSSI_PREFIX = ")]}'\n"


@pytest.fixture
def client() -> GerritClient:
    return GerritClient(
        base_url="https://review.example.com",
        username="testuser",
        token="s3cr3t",
    )


class TestGerritClientInit:
    def test_base_url_trailing_slash_stripped(self) -> None:
        c = GerritClient(base_url="https://review.example.com/", username="u", token="t")
        assert c._base_url == "https://review.example.com"

    def test_session_basic_auth_set(self) -> None:
        c = GerritClient(base_url="https://review.example.com", username="alice", token="pw")
        assert c._session.auth == ("alice", "pw")

    def test_session_accept_header(self) -> None:
        c = GerritClient(base_url="https://review.example.com", username="u", token="t")
        assert c._session.headers["Accept"] == "application/json"


class TestXssiStripping:
    def test_strips_xssi_prefix(self, client: GerritClient) -> None:
        assert client._parse(XSSI_PREFIX + '{"key": 1}') == {"key": 1}

    def test_no_prefix_parses_normally(self, client: GerritClient) -> None:
        assert client._parse('{"key": "value"}') == {"key": "value"}

    def test_strips_prefix_from_list(self, client: GerritClient) -> None:
        assert client._parse(XSSI_PREFIX + "[1, 2, 3]") == [1, 2, 3]


class TestGerritClientGet:
    def test_get_returns_parsed_json(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = XSSI_PREFIX + '[{"_number": 1}]'
        with patch.object(client._session, "get", return_value=mock_resp) as mock_get:
            result = client.get("/changes/", params={"q": "status:open"})
        mock_get.assert_called_once_with("https://review.example.com/changes/", params={"q": "status:open"})
        assert result == [{"_number": 1}]

    def test_get_raises_on_http_error(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        with patch.object(client._session, "get", return_value=mock_resp):
            with pytest.raises(GerritApiError, match="404"):
                client.get("/changes/99999999")

    def test_get_without_params(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = '{"id": "abc"}'
        with patch.object(client._session, "get", return_value=mock_resp):
            result = client.get("/changes/12345")
        assert result == {"id": "abc"}


class TestGerritClientPost:
    def test_post_with_payload_returns_parsed_json(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = '{"_number": 99}'
        with patch.object(client._session, "post", return_value=mock_resp) as mock_post:
            result = client.post("/changes/", payload={"project": "p", "branch": "main", "subject": "s"})
        mock_post.assert_called_once()
        assert result == {"_number": 99}

    def test_post_empty_body_returns_none(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = ""
        with patch.object(client._session, "post", return_value=mock_resp):
            result = client.post("/changes/12345/ready")
        assert result is None

    def test_post_raises_on_http_error(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 409
        mock_resp.text = "Conflict"
        with patch.object(client._session, "post", return_value=mock_resp):
            with pytest.raises(GerritApiError, match="409"):
                client.post("/changes/12345/abandon")


class TestGerritClientPut:
    def test_put_with_payload_returns_parsed_json(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = '"my-topic"'
        with patch.object(client._session, "put", return_value=mock_resp):
            result = client.put("/changes/12345/topic", payload={"topic": "my-topic"})
        assert result == "my-topic"

    def test_put_empty_body_returns_none(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = "   "
        with patch.object(client._session, "put", return_value=mock_resp):
            result = client.put("/changes/12345/topic", payload={"topic": ""})
        assert result is None

    def test_put_raises_on_http_error(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 403
        mock_resp.text = "Forbidden"
        with patch.object(client._session, "put", return_value=mock_resp):
            with pytest.raises(GerritApiError, match="403"):
                client.put("/changes/12345/topic", payload={"topic": "x"})


class TestVerifySsl:
    def test_default_true(self) -> None:
        c = GerritClient(base_url="https://review.example.com", username="u", token="t")
        assert c._session.verify is True

    def test_set_to_false(self) -> None:
        c = GerritClient(base_url="https://review.example.com", username="u", token="t", verify_ssl=False)
        assert c._session.verify is False


class TestGetRaw:
    def test_returns_stripped_text(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = XSSI_PREFIX + "SGVsbG8gV29ybGQ="
        with patch.object(client._session, "get", return_value=mock_resp):
            result = client.get_raw("/projects/p/branches/b/files/f/content")
        assert result == "SGVsbG8gV29ybGQ="

    def test_without_xssi_prefix(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = "SGVsbG8="
        with patch.object(client._session, "get", return_value=mock_resp):
            result = client.get_raw("/some/endpoint")
        assert result == "SGVsbG8="

    def test_raises_on_http_error(self, client: GerritClient) -> None:
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        with patch.object(client._session, "get", return_value=mock_resp):
            with pytest.raises(GerritApiError, match="404"):
                client.get_raw("/not/found")


class TestEncodeProjectName:
    def test_encodes_slashes(self) -> None:
        assert encode_project_name("my/project") == "my%2Fproject"

    def test_no_encoding_needed(self) -> None:
        assert encode_project_name("simple-project") == "simple-project"

    def test_encodes_spaces(self) -> None:
        assert encode_project_name("my project") == "my%20project"
