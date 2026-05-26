"""
基底スクレイパークラス
"""

import time
import random
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from config import DEFAULT_HEADERS, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX


class BaseScraper(ABC):
    def __init__(
        self,
        delay_min: float = REQUEST_DELAY_MIN,
        delay_max: float = REQUEST_DELAY_MAX,
    ):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.delay_min = delay_min
        self.delay_max = delay_max

    def _wait(self):
        """リクエスト前に待機する（礼儀正しいクローリング）"""
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def get_soup(self, url: str, **kwargs) -> BeautifulSoup:
        """GETリクエストを送り BeautifulSoup を返す"""
        self._wait()
        resp = self.session.get(url, timeout=15, **kwargs)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "lxml")

    @abstractmethod
    def scrape(self) -> list[dict]:
        """
        スポット情報を収集して返す。
        各要素は以下のキーを持つ辞書:
          - name: str
          - description: str | None
          - category: str
          - latitude: float
          - longitude: float
          - source: str
          - source_url: str | None
          - tags: list[str]
          - prefecture: str  ("tokyo" | "kanagawa")
        """
        ...
