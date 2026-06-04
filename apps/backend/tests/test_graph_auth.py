from unittest.mock import patch

from app.services.graph_auth import GraphAuthService


def test_graph_auth_service_creates_client_secret_credential():
    with patch("app.services.graph_auth.ClientSecretCredential") as mock_cred_cls:

        GraphAuthService(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="secret-789",
        )
        mock_cred_cls.assert_called_once_with(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="secret-789",
        )


def test_graph_auth_service_get_credential_returns_credential():
    with patch("app.services.graph_auth.ClientSecretCredential") as mock_cred_cls:
        service = GraphAuthService("t", "c", "s")
        credential = service.get_credential()
        assert credential is mock_cred_cls.return_value


def test_graph_auth_service_get_client_returns_graph_service_client():
    with patch("app.services.graph_auth.ClientSecretCredential"), patch(
        "app.services.graph_auth.GraphServiceClient"
    ) as mock_graph_cls:
        service = GraphAuthService("t", "c", "s")
        client = service.get_client()
        mock_graph_cls.assert_called_once()
        assert client is mock_graph_cls.return_value


def test_graph_auth_service_get_client_passes_credential():
    with patch(
        "app.services.graph_auth.ClientSecretCredential"
    ) as mock_cred_cls, patch(
        "app.services.graph_auth.GraphServiceClient"
    ) as mock_graph_cls:
        service = GraphAuthService("t", "c", "s")
        service.get_client()
        mock_graph_cls.assert_called_once_with(credentials=mock_cred_cls.return_value)
