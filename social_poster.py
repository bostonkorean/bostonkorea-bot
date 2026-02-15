#!/usr/bin/env python3
"""
소셜미디어 자동 포스팅 모듈
- XPoster: tweepy를 사용한 X(트위터) 포스팅
- InstagramPoster: instagrapi를 사용한 인스타그램 포스팅
"""

import os
import tempfile
import requests


class XPoster:
    """X(트위터) 포스팅 클래스"""

    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
        import tweepy
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

    def post(self, text: str) -> str:
        """트윗 게시. 성공 시 트윗 ID 반환."""
        response = self.client.create_tweet(text=text)
        return str(response.data["id"])

    def test_connection(self) -> bool:
        """연결 테스트. 인증된 사용자 정보 조회."""
        me = self.client.get_me()
        return me.data is not None


class InstagramPoster:
    """인스타그램 포스팅 클래스"""

    def __init__(self, username: str, password: str):
        from instagrapi import Client
        self.client = Client()
        self.username = username
        self.password = password
        self._logged_in = False

    def _login(self):
        if not self._logged_in:
            self.client.login(self.username, self.password)
            self._logged_in = True

    def post(self, caption: str, image_url: str) -> str:
        """이미지 다운로드 후 인스타그램에 게시. 성공 시 미디어 ID 반환."""
        self._login()

        # 이미지 다운로드
        tmp_path = None
        try:
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()

            suffix = ".jpg"
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
            os.close(tmp_fd)
            with open(tmp_path, "wb") as f:
                f.write(resp.content)

            media = self.client.photo_upload(tmp_path, caption)
            return str(media.pk)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_connection(self) -> bool:
        """로그인 테스트."""
        self._login()
        return self._logged_in
