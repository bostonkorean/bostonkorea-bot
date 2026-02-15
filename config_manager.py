#!/usr/bin/env python3
"""
설정 관리 모듈 - config.json에서 API 키/비밀번호 로드/저장
"""

import json
import os
import sys

# PyInstaller exe일 때는 exe 위치, 아니면 스크립트 위치
if getattr(sys, 'frozen', False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(_APP_DIR, "config.json")

DEFAULT_CONFIG = {
    "x": {
        "api_key": "",
        "api_secret": "",
        "access_token": "",
        "access_token_secret": ""
    },
    "instagram": {
        "username": "",
        "password": ""
    }
}


def load_config() -> dict:
    """config.json에서 설정 로드. 파일이 없으면 기본값 반환."""
    if not os.path.exists(CONFIG_FILE):
        return json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        # 누락된 키가 있으면 기본값으로 채움
        for section in DEFAULT_CONFIG:
            if section not in config:
                config[section] = DEFAULT_CONFIG[section].copy()
            else:
                for key in DEFAULT_CONFIG[section]:
                    if key not in config[section]:
                        config[section][key] = DEFAULT_CONFIG[section][key]
        return config
    except (json.JSONDecodeError, IOError):
        return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(config: dict) -> None:
    """설정을 config.json에 저장."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def is_x_configured(config: dict) -> bool:
    """X API 키가 모두 입력되어 있는지 확인."""
    x = config.get("x", {})
    return all(x.get(k) for k in ("api_key", "api_secret", "access_token", "access_token_secret"))


def is_instagram_configured(config: dict) -> bool:
    """인스타그램 계정 정보가 입력되어 있는지 확인."""
    ig = config.get("instagram", {})
    return all(ig.get(k) for k in ("username", "password"))
