from __future__ import annotations

from urllib.parse import quote_plus


class ScholarService:

    HOME_URL = "https://scholar.google.com/"

    def build_search_url(self, query: str) -> str:
        if not query.strip():
            raise ValueError("检索关键词不能为空")
        return f"{self.HOME_URL}scholar?q={quote_plus(query.strip())}"
