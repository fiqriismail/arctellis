from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient


class GraphAuthService:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str) -> None:
        self._credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

    def get_credential(self) -> ClientSecretCredential:
        return self._credential

    def get_client(self) -> GraphServiceClient:
        """Return a new GraphServiceClient backed by the stored credential."""
        return GraphServiceClient(credentials=self._credential)
