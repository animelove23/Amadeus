from __future__ import annotations

import re
import hashlib
import time
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.parse import urlencode

import requests


@dataclass(frozen=True)
class BilibiliVideoResult:
    title: str
    url: str
    bvid: str


class BilibiliService:
    """封装 B 站搜索访问，避免把 HTTP 细节塞进 Agent。"""

    NAV_ENDPOINT = "https://api.bilibili.com/x/web-interface/nav"
    SEARCH_ENDPOINT = "https://api.bilibili.com/x/web-interface/wbi/search/type"
    TITLE_TAG_PATTERN = re.compile(r"<[^>]+>")
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
        27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
        37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
        22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44,
        52,
    ]

    def search_first_video(self, query: str) -> BilibiliVideoResult:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")

        session = requests.Session()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com/",
        }

        signed_params = self._build_signed_params(
            session=session,
            headers=headers,
            params={
                "search_type": "video",
                "keyword": query.strip(),
                "page": 1,
            },
        )

        response = session.get(
            self.SEARCH_ENDPOINT,
            params=signed_params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()

        payload: dict[str, Any] = response.json()
        result_items = payload.get("data", {}).get("result", [])
        if not result_items:
            raise LookupError("没有找到视频搜索结果")

        first_video = result_items[0]
        bvid = first_video.get("bvid")
        if not isinstance(bvid, str) or not bvid:
            raise ValueError("搜索结果缺少 bvid")

        raw_title = first_video.get("title", "")
        title = self._clean_title(raw_title)
        return BilibiliVideoResult(
            title=title,
            url=f"https://www.bilibili.com/video/{bvid}",
            bvid=bvid,
        )

    def _clean_title(self, title: str) -> str:
        return unescape(self.TITLE_TAG_PATTERN.sub("", title))

    def _build_signed_params(
        self,
        session: requests.Session,
        headers: dict[str, str],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        nav_payload = session.get(
            self.NAV_ENDPOINT,
            headers=headers,
            timeout=10,
        ).json()

        wbi_img = nav_payload.get("data", {}).get("wbi_img", {})
        img_key = self._extract_wbi_key(wbi_img.get("img_url", ""))
        sub_key = self._extract_wbi_key(wbi_img.get("sub_url", ""))
        if not img_key or not sub_key:
            raise ValueError("无法获取 B 站 WBI 签名密钥")

        raw_wbi_key = img_key + sub_key
        mixin_key = "".join(raw_wbi_key[index] for index in self.MIXIN_KEY_ENC_TAB)[:32]

        signed_params = {
            key: self._filter_value(value)
            for key, value in {
                **params,
                "wts": int(time.time()),
            }.items()
        }
        query = urlencode(sorted(signed_params.items()))
        signed_params["w_rid"] = hashlib.md5((query + mixin_key).encode()).hexdigest()
        return signed_params

    def _extract_wbi_key(self, url: str) -> str:
        if not isinstance(url, str) or not url:
            return ""
        return url.rsplit("/", 1)[-1].split(".")[0]

    def _filter_value(self, value: Any) -> str:
        return "".join(character for character in str(value) if character not in "!'()*")
