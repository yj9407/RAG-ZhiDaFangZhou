import asyncio
from typing import Optional

from app.clients.simple_search_engine import SimpleSearchClient
from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    def __init__(self, es_config: ESConfig):
        self.es_config = es_config
        self.client: Optional[SimpleSearchClient] = None

    def init(self):
        self.client = SimpleSearchClient()

    async def close(self):
        await self.client.close()


es_client_manager = ESClientManager(app_config.es)
