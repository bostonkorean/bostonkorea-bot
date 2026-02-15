#!/usr/bin/env python3
"""
미디어 생성 모듈
- CardGenerator: 기사 카드 이미지 생성 (PIL)
- VideoGenerator: 카드 이미지로 줌 효과 동영상 생성 (imageio)
"""

import os
import tempfile

import requests
from PIL import Image, ImageDraw, ImageFont


def _find_font(bold=False):
    """한국어 지원 폰트 찾기."""
    candidates = [
        # Nanum (Linux / 설치된 경우)
        "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        # Windows
        "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf",
        # macOS
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleSDGothicNeo.ttc",
        # Noto Sans CJK (Linux)
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        # DejaVu fallback
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _load_font(size, bold=False):
    """지정 크기의 폰트 로드."""
    path = _find_font(bold)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _download_image(url):
    """URL에서 이미지 다운로드하여 PIL Image 반환."""
    resp = requests.get(url, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    resp.raise_for_status()
    fd, tmp = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    with open(tmp, "wb") as f:
        f.write(resp.content)
    img = Image.open(tmp).convert("RGB")
    os.unlink(tmp)
    return img


def _crop_to_fill(img, target_w, target_h):
    """이미지를 대상 크기에 맞게 크롭 + 리사이즈."""
    img_w, img_h = img.size
    target_ratio = target_w / target_h
    img_ratio = img_w / img_h

    if img_ratio > target_ratio:
        new_h = img_h
        new_w = int(img_h * target_ratio)
        left = (img_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, new_h))
    else:
        new_w = img_w
        new_h = int(img_w / target_ratio)
        top = (img_h - new_h) // 2
        img = img.crop((0, top, new_w, top + new_h))

    return img.resize((target_w, target_h), Image.LANCZOS)


def _wrap_text(text, font, max_width, draw):
    """텍스트를 최대 너비에 맞게 줄바꿈."""
    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line

    if current_line:
        lines.append(current_line)

    return lines[:4]  # 최대 4줄


class CardGenerator:
    """카드형 이미지 생성기"""

    CARD_SIZE = (1080, 1080)

    def generate(self, title, category, image_source, output_path=None):
        """
        카드 이미지 생성.

        Args:
            title: 기사 제목
            category: 카테고리 문자열
            image_source: 이미지 URL 또는 로컬 파일 경로 (None이면 기본 배경 사용)
            output_path: 저장 경로 (None이면 임시 파일)

        Returns:
            (PIL.Image, 저장 경로) 튜플
        """
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)

        w, h = self.CARD_SIZE

        # 배경 이미지 로드
        if image_source:
            try:
                if image_source.startswith("http"):
                    bg_img = _download_image(image_source)
                else:
                    bg_img = Image.open(image_source).convert("RGB")
                bg = _crop_to_fill(bg_img, w, h)
            except Exception:
                bg = self._create_default_background(w, h)
        else:
            bg = self._create_default_background(w, h)

        # RGBA 변환 및 그라데이션 오버레이
        card = bg.convert("RGBA")
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        # 하단 60% 그라데이션
        gradient_start = int(h * 0.4)
        for y in range(gradient_start, h):
            progress = (y - gradient_start) / (h - gradient_start)
            alpha = int(220 * progress)
            draw_overlay.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

        card = Image.alpha_composite(card, overlay)
        draw = ImageDraw.Draw(card)

        # 폰트
        title_font = _load_font(52, bold=True)
        cat_font = _load_font(26, bold=True)
        brand_font = _load_font(22, bold=False)

        # 카테고리 뱃지 (좌상단)
        if category:
            cat_text = f"  {category}  "
            cat_bbox = draw.textbbox((0, 0), cat_text, font=cat_font)
            cat_w = cat_bbox[2] - cat_bbox[0]
            cat_h = cat_bbox[3] - cat_bbox[1]
            pad = 8
            draw.rounded_rectangle(
                [40, 40, 40 + cat_w + pad * 2, 40 + cat_h + pad * 2],
                radius=8,
                fill=(220, 50, 50, 200),
            )
            draw.text((40 + pad, 40 + pad), cat_text, font=cat_font, fill="white")

        # 제목 (하단)
        margin = 60
        max_text_width = w - margin * 2
        lines = _wrap_text(title, title_font, max_text_width, draw)

        line_height = 64
        total_text_h = len(lines) * line_height
        text_y = h - 140 - total_text_h

        for line in lines:
            # 그림자
            draw.text((margin + 2, text_y + 2), line, font=title_font, fill=(0, 0, 0, 180))
            draw.text((margin, text_y), line, font=title_font, fill="white")
            text_y += line_height

        # 브랜딩 (하단)
        brand_text = "보스톤코리아  |  bostonkorea.com"
        draw.text((margin, h - 65), brand_text, font=brand_font, fill=(200, 200, 200, 220))

        card_rgb = card.convert("RGB")
        card_rgb.save(output_path, "PNG", quality=95)
        return card_rgb, output_path

    def _create_default_background(self, w, h):
        """이미지가 없을 때 기본 그라데이션 배경."""
        bg = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(bg)
        for y in range(h):
            r = int(20 + 30 * (y / h))
            g = int(30 + 20 * (y / h))
            b = int(60 + 40 * (y / h))
            draw.line([(0, y), (w, y)], fill=(r, g, b))
        return bg


class VideoGenerator:
    """카드 이미지에서 줌 효과 동영상 생성"""

    def generate(self, card_image_path, output_path=None, duration=5, fps=24):
        """
        카드 이미지로 줌 효과 동영상 생성.

        Args:
            card_image_path: 카드 이미지 파일 경로
            output_path: 출력 동영상 경로 (None이면 임시 파일)
            duration: 동영상 길이 (초)
            fps: 프레임 레이트

        Returns:
            출력 파일 경로
        """
        import numpy as np
        import imageio

        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".mp4")
            os.close(fd)

        img = Image.open(card_image_path).convert("RGB")
        w, h = img.size

        total_frames = duration * fps
        writer = imageio.get_writer(output_path, fps=fps, macro_block_size=1)

        for i in range(total_frames):
            t = i / total_frames
            # 느린 줌인: 1.0 → 1.12
            zoom = 1.0 + 0.12 * t

            new_w = int(w / zoom)
            new_h = int(h / zoom)
            left = (w - new_w) // 2
            top = (h - new_h) // 2

            cropped = img.crop((left, top, left + new_w, top + new_h))
            resized = cropped.resize((w, h), Image.LANCZOS)
            writer.append_data(np.array(resized))

        writer.close()
        return output_path
