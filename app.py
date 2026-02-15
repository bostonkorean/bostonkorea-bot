#!/usr/bin/env python3
"""
보스톤코리아 소셜미디어 포스팅 봇 - 데스크탑 앱
"""

import os
import sys
import platform
import subprocess
import customtkinter as ctk
from tkinter import messagebox
import threading
from PIL import Image
from bostonkorea_bot import BostonKoreaBot
from config_manager import load_config, save_config, is_x_configured, is_instagram_configured
from social_poster import XPoster, InstagramPoster
from media_generator import CardGenerator, VideoGenerator

# 테마 설정
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 앱 기본 경로 (PyInstaller exe일 때는 exe 위치, 아니면 스크립트 위치)
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# 생성 파일 저장 디렉토리
GENERATED_DIR = os.path.join(APP_DIR, "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)


class BostonKoreaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.bot = BostonKoreaBot()
        self.articles = []
        self.current_article = None
        self.config = load_config()
        self.current_result = None
        self.card_image_path = None
        self.video_path = None
        self._preview_image_ref = None  # CTkImage 참조 유지 (GC 방지)

        # 윈도우 설정
        self.title("보스톤코리아 소셜미디어 봇")
        self.geometry("1000x750")
        self.minsize(900, 650)

        # 메인 레이아웃
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_main_content()
        self._create_footer()

        # 시작 시 기사 로드
        self.after(100, self.load_articles)

    def _create_header(self):
        """헤더 영역"""
        header = ctk.CTkFrame(self, height=60)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_columnconfigure(1, weight=1)

        # 타이틀
        title = ctk.CTkLabel(
            header,
            text="보스톤코리아 소셜미디어 봇",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, padx=15, pady=15)

        # 카테고리 선택
        self.category_var = ctk.StringVar(value="전체")
        categories = list(self.bot.get_categories().keys())

        category_label = ctk.CTkLabel(header, text="카테고리:")
        category_label.grid(row=0, column=1, padx=(20, 5), pady=15, sticky="e")

        self.category_menu = ctk.CTkOptionMenu(
            header,
            variable=self.category_var,
            values=categories,
            command=self.on_category_change,
            width=120
        )
        self.category_menu.grid(row=0, column=2, padx=5, pady=15)

        # 새로고침 버튼
        self.refresh_btn = ctk.CTkButton(
            header,
            text="새로고침",
            command=self.load_articles,
            width=100
        )
        self.refresh_btn.grid(row=0, column=3, padx=(15, 5), pady=15)

        # 설정 버튼
        settings_btn = ctk.CTkButton(
            header,
            text="설정",
            command=self.open_settings,
            width=80,
            fg_color="gray40",
            hover_color="gray30"
        )
        settings_btn.grid(row=0, column=4, padx=(5, 15), pady=15)

    def _create_main_content(self):
        """메인 컨텐츠 영역"""
        main = ctk.CTkFrame(self)
        main.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=3)
        main.grid_rowconfigure(0, weight=1)

        # 왼쪽: 기사 목록
        self._create_article_list(main)

        # 오른쪽: 결과 패널 (탭 구조)
        self._create_result_panel(main)

    def _create_article_list(self, parent):
        """기사 목록 패널"""
        list_frame = ctk.CTkFrame(parent)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        list_frame.grid_rowconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # 헤더
        list_header = ctk.CTkLabel(
            list_frame,
            text="최신 기사",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_header.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        # 스크롤 가능한 기사 목록
        self.article_scroll = ctk.CTkScrollableFrame(list_frame)
        self.article_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.article_scroll.grid_columnconfigure(0, weight=1)

        # 로딩 표시
        self.loading_label = ctk.CTkLabel(
            self.article_scroll,
            text="기사를 불러오는 중...",
            font=ctk.CTkFont(size=14)
        )
        self.loading_label.grid(row=0, column=0, pady=50)

    def _create_result_panel(self, parent):
        """결과 패널 (탭: 텍스트 / 미리보기)"""
        result_frame = ctk.CTkFrame(parent)
        result_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # 탭뷰
        self.result_tabs = ctk.CTkTabview(result_frame)
        self.result_tabs.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # ========== 텍스트 탭 ==========
        text_tab = self.result_tabs.add("텍스트")
        text_tab.grid_rowconfigure(1, weight=1)
        text_tab.grid_rowconfigure(3, weight=1)
        text_tab.grid_columnconfigure(0, weight=1)

        # X 섹션
        x_header_frame = ctk.CTkFrame(text_tab, fg_color="transparent")
        x_header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        x_header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            x_header_frame,
            text="X (트위터)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self.x_copy_btn = ctk.CTkButton(
            x_header_frame, text="복사",
            command=lambda: self.copy_to_clipboard("x"),
            width=60, height=28
        )
        self.x_copy_btn.grid(row=0, column=1, padx=(0, 5))

        self.x_post_btn = ctk.CTkButton(
            x_header_frame, text="X에 게시",
            command=self.post_to_x,
            width=80, height=28,
            fg_color="#1DA1F2", hover_color="#1891DB"
        )
        self.x_post_btn.grid(row=0, column=2)

        self.x_textbox = ctk.CTkTextbox(text_tab, height=150)
        self.x_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # 인스타그램 섹션
        ig_header_frame = ctk.CTkFrame(text_tab, fg_color="transparent")
        ig_header_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(10, 5))
        ig_header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            ig_header_frame,
            text="인스타그램",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self.ig_copy_btn = ctk.CTkButton(
            ig_header_frame, text="복사",
            command=lambda: self.copy_to_clipboard("instagram"),
            width=60, height=28
        )
        self.ig_copy_btn.grid(row=0, column=1, padx=(0, 5))

        self.ig_post_btn = ctk.CTkButton(
            ig_header_frame, text="인스타에 게시",
            command=self.post_to_instagram,
            width=100, height=28,
            fg_color="#E1306C", hover_color="#C13584"
        )
        self.ig_post_btn.grid(row=0, column=2)

        self.ig_textbox = ctk.CTkTextbox(text_tab, height=200)
        self.ig_textbox.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # 초기 안내 메시지
        self.x_textbox.insert("1.0", "← 왼쪽에서 기사를 선택하세요")
        self.ig_textbox.insert("1.0", "← 왼쪽에서 기사를 선택하세요")
        self.x_textbox.configure(state="disabled")
        self.ig_textbox.configure(state="disabled")

        # ========== 미리보기 탭 ==========
        preview_tab = self.result_tabs.add("미리보기")
        preview_tab.grid_rowconfigure(1, weight=1)
        preview_tab.grid_columnconfigure(0, weight=1)

        # 미리보기 헤더 (카드 이미지 / 동영상 전환)
        preview_header = ctk.CTkFrame(preview_tab, fg_color="transparent")
        preview_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        preview_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_header,
            text="카드 미리보기",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self.gen_video_btn = ctk.CTkButton(
            preview_header, text="동영상 생성",
            command=self.generate_video,
            width=100, height=28,
            fg_color="#9B59B6", hover_color="#8E44AD"
        )
        self.gen_video_btn.grid(row=0, column=1, padx=(0, 5))

        self.play_video_btn = ctk.CTkButton(
            preview_header, text="재생",
            command=self.play_video,
            width=60, height=28,
            state="disabled"
        )
        self.play_video_btn.grid(row=0, column=2)

        # 카드 미리보기 이미지 영역
        self.preview_container = ctk.CTkFrame(preview_tab, fg_color="transparent")
        self.preview_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.preview_container.grid_rowconfigure(0, weight=1)
        self.preview_container.grid_columnconfigure(0, weight=1)

        self.preview_image_label = ctk.CTkLabel(
            self.preview_container,
            text="기사를 선택하면\n카드 미리보기가 표시됩니다",
            font=ctk.CTkFont(size=14),
        )
        self.preview_image_label.grid(row=0, column=0, sticky="nsew")

        # 동영상 상태
        self.video_status_label = ctk.CTkLabel(
            preview_tab,
            text="",
            font=ctk.CTkFont(size=12),
        )
        self.video_status_label.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")

    def _create_footer(self):
        """푸터 영역"""
        footer = ctk.CTkFrame(self, height=40)
        footer.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))

        self.status_label = ctk.CTkLabel(
            footer,
            text="준비됨",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=15, pady=10)

        # URL 직접 입력
        self.url_entry = ctk.CTkEntry(
            footer,
            placeholder_text="기사 URL 직접 입력...",
            width=300
        )
        self.url_entry.pack(side="right", padx=(5, 15), pady=10)

        url_btn = ctk.CTkButton(
            footer,
            text="URL 로드",
            command=self.load_from_url,
            width=80
        )
        url_btn.pack(side="right", padx=5, pady=10)

    # ===== 기사 로드 / 표시 =====

    def load_articles(self):
        """기사 목록 로드"""
        self.refresh_btn.configure(state="disabled")
        self.status_label.configure(text="기사를 불러오는 중...")

        def fetch():
            category = self.bot.get_categories().get(self.category_var.get(), '')
            articles = self.bot.fetch_latest_articles(category=category, limit=15)
            self.after(0, lambda: self.display_articles(articles))

        threading.Thread(target=fetch, daemon=True).start()

    def display_articles(self, articles):
        """기사 목록 표시"""
        self.articles = articles

        for widget in self.article_scroll.winfo_children():
            widget.destroy()

        if not articles:
            ctk.CTkLabel(
                self.article_scroll,
                text="기사가 없습니다",
                font=ctk.CTkFont(size=14)
            ).grid(row=0, column=0, pady=50)
        else:
            for i, article in enumerate(articles):
                self._create_article_card(i, article)

        self.refresh_btn.configure(state="normal")
        self.status_label.configure(text=f"{len(articles)}개 기사 로드됨")

    def _create_article_card(self, index, article):
        """기사 카드 생성"""
        card = ctk.CTkFrame(self.article_scroll, corner_radius=8)
        card.grid(row=index, column=0, sticky="ew", pady=5, padx=5)
        card.grid_columnconfigure(0, weight=1)

        title_btn = ctk.CTkButton(
            card,
            text=article['title'],
            font=ctk.CTkFont(size=13),
            anchor="w",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=lambda a=article: self.select_article(a)
        )
        title_btn.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        if article.get('category'):
            ctk.CTkLabel(
                card,
                text=article['category'],
                font=ctk.CTkFont(size=11),
                fg_color=("gray80", "gray25"),
                corner_radius=4
            ).grid(row=0, column=1, padx=10, pady=10)

    # ===== 기사 선택 / 변환 =====

    def select_article(self, article):
        """기사 선택 및 변환"""
        self.status_label.configure(text="기사를 변환하는 중...")
        self.current_article = article
        self.card_image_path = None
        self.video_path = None
        self.play_video_btn.configure(state="disabled")
        self.video_status_label.configure(text="")

        def process():
            try:
                full_article = self.bot.fetch_article(article['url'])
                result = self.bot.format_for_both(full_article)
                self.after(0, lambda: self.display_result(result, full_article))
            except Exception as e:
                self.after(0, lambda: self.show_error(str(e)))

        threading.Thread(target=process, daemon=True).start()

    def display_result(self, result, full_article=None):
        """결과 표시 + 카드 미리보기 생성"""
        self.current_result = result

        # X 텍스트
        self.x_textbox.configure(state="normal")
        self.x_textbox.delete("1.0", "end")
        self.x_textbox.insert("1.0", result['x'])

        # 인스타그램 텍스트
        self.ig_textbox.configure(state="normal")
        self.ig_textbox.delete("1.0", "end")
        self.ig_textbox.insert("1.0", result['instagram'])

        self.status_label.configure(text="변환 완료! 카드 생성 중...")

        # 카드 미리보기 생성 (백그라운드)
        image_url = result.get('image_url', '')
        title = full_article['title'] if full_article else "제목 없음"
        category = full_article.get('category', '') if full_article else ''

        def gen_card():
            try:
                generator = CardGenerator()
                output = os.path.join(GENERATED_DIR, "card_preview.png")
                _, path = generator.generate(title, category, image_url, output)
                self.card_image_path = path
                self.after(0, lambda: self._show_card_preview(path))
            except Exception as e:
                self.after(0, lambda: self._on_card_error(str(e)))

        threading.Thread(target=gen_card, daemon=True).start()

    def _show_card_preview(self, card_path):
        """카드 미리보기 표시"""
        try:
            pil_img = Image.open(card_path)

            # 프리뷰 크기 계산 (가용 영역에 맞춤, 최대 420x420)
            display_size = (420, 420)
            self._preview_image_ref = ctk.CTkImage(
                light_image=pil_img,
                dark_image=pil_img,
                size=display_size
            )
            self.preview_image_label.configure(
                image=self._preview_image_ref,
                text=""
            )
            self.status_label.configure(text="카드 미리보기 완료!")
        except Exception as e:
            self.preview_image_label.configure(text=f"미리보기 오류: {e}")
            self.status_label.configure(text="카드 생성 실패")

    def _on_card_error(self, error):
        """카드 생성 실패"""
        self.preview_image_label.configure(text=f"카드 생성 실패:\n{error}")
        self.status_label.configure(text="카드 생성 실패")

    # ===== 동영상 생성 / 재생 =====

    def generate_video(self):
        """카드 이미지로 동영상 생성"""
        if not self.card_image_path:
            messagebox.showwarning("알림", "먼저 기사를 선택하세요. 카드 이미지가 필요합니다.")
            return

        self.gen_video_btn.configure(state="disabled")
        self.play_video_btn.configure(state="disabled")
        self.video_status_label.configure(text="동영상 생성 중...")
        self.status_label.configure(text="동영상 생성 중...")

        def on_progress(pct):
            self.after(0, lambda: self.video_status_label.configure(
                text=f"동영상 생성 중... {pct}%"))

        def do_gen():
            try:
                generator = VideoGenerator()
                output = os.path.join(GENERATED_DIR, "card_video.mp4")
                path = generator.generate(
                    self.card_image_path, output,
                    on_progress=on_progress)
                self.video_path = path
                self.after(0, lambda: self._on_video_success(path))
            except Exception as e:
                self.after(0, lambda: self._on_video_error(str(e)))

        threading.Thread(target=do_gen, daemon=True).start()

    def _on_video_success(self, path):
        """동영상 생성 성공"""
        self.gen_video_btn.configure(state="normal")
        self.play_video_btn.configure(state="normal")
        size_mb = os.path.getsize(path) / (1024 * 1024)
        self.video_status_label.configure(text=f"동영상 생성 완료 ({size_mb:.1f}MB): {os.path.basename(path)}")
        self.status_label.configure(text="동영상 생성 완료!")

    def _on_video_error(self, error):
        """동영상 생성 실패"""
        self.gen_video_btn.configure(state="normal")
        self.video_status_label.configure(text=f"동영상 생성 실패: {error}")
        self.status_label.configure(text="동영상 생성 실패")
        messagebox.showerror("오류", f"동영상 생성 중 오류:\n{error}")

    def play_video(self):
        """생성된 동영상을 시스템 기본 플레이어로 재생"""
        if not self.video_path or not os.path.exists(self.video_path):
            messagebox.showwarning("알림", "재생할 동영상이 없습니다. 먼저 동영상을 생성하세요.")
            return

        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(self.video_path)
            elif system == "Darwin":
                subprocess.Popen(["open", self.video_path])
            else:
                subprocess.Popen(["xdg-open", self.video_path])
        except Exception as e:
            messagebox.showerror("오류", f"동영상 재생 실패:\n{e}\n\n파일 위치: {self.video_path}")

    # ===== 복사 / URL 로드 =====

    def copy_to_clipboard(self, platform_name):
        """클립보드에 복사"""
        if platform_name == "x":
            text = self.x_textbox.get("1.0", "end-1c")
        else:
            text = self.ig_textbox.get("1.0", "end-1c")

        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_label.configure(text=f"{'X' if platform_name == 'x' else '인스타그램'}용 텍스트 복사됨!")

    def load_from_url(self):
        """URL에서 직접 로드"""
        url = self.url_entry.get().strip()
        if not url:
            return

        if not url.startswith('http'):
            messagebox.showerror("오류", "올바른 URL을 입력하세요")
            return

        self.select_article({'url': url, 'title': 'URL에서 로드'})
        self.url_entry.delete(0, "end")

    def on_category_change(self, value):
        """카테고리 변경"""
        self.load_articles()

    # ===== 소셜미디어 게시 =====

    def post_to_x(self):
        """X에 게시"""
        text = self.x_textbox.get("1.0", "end-1c").strip()
        if not text or text == "← 왼쪽에서 기사를 선택하세요":
            messagebox.showwarning("알림", "먼저 기사를 선택하세요.")
            return

        if not is_x_configured(self.config):
            messagebox.showwarning("설정 필요", "X API 키가 설정되지 않았습니다.\n설정 버튼에서 API 키를 입력하세요.")
            return

        self.x_post_btn.configure(state="disabled")
        self.status_label.configure(text="X에 게시하는 중...")

        def do_post():
            try:
                x_cfg = self.config["x"]
                poster = XPoster(
                    x_cfg["api_key"], x_cfg["api_secret"],
                    x_cfg["access_token"], x_cfg["access_token_secret"]
                )
                tweet_id = poster.post(text)
                self.after(0, lambda: self._on_post_success("X", tweet_id))
            except Exception as e:
                self.after(0, lambda: self._on_post_error("X", str(e)))

        threading.Thread(target=do_post, daemon=True).start()

    def post_to_instagram(self):
        """인스타그램에 게시"""
        caption = self.ig_textbox.get("1.0", "end-1c").strip()
        if not caption or caption == "← 왼쪽에서 기사를 선택하세요":
            messagebox.showwarning("알림", "먼저 기사를 선택하세요.")
            return

        if not is_instagram_configured(self.config):
            messagebox.showwarning("설정 필요", "인스타그램 계정 정보가 설정되지 않았습니다.\n설정 버튼에서 계정 정보를 입력하세요.")
            return

        image_url = self.current_result.get("image_url", "") if self.current_result else ""
        if not image_url:
            messagebox.showwarning("알림", "이미지가 없는 기사는 인스타그램에 게시할 수 없습니다.")
            return

        self.ig_post_btn.configure(state="disabled")
        self.status_label.configure(text="인스타그램에 게시하는 중...")

        def do_post():
            try:
                ig_cfg = self.config["instagram"]
                poster = InstagramPoster(ig_cfg["username"], ig_cfg["password"])
                media_id = poster.post(caption, image_url)
                self.after(0, lambda: self._on_post_success("인스타그램", media_id))
            except Exception as e:
                self.after(0, lambda: self._on_post_error("인스타그램", str(e)))

        threading.Thread(target=do_post, daemon=True).start()

    def _on_post_success(self, platform_name, post_id):
        """게시 성공 콜백"""
        self.status_label.configure(text=f"{platform_name} 게시 완료! (ID: {post_id})")
        self.x_post_btn.configure(state="normal")
        self.ig_post_btn.configure(state="normal")
        messagebox.showinfo("성공", f"{platform_name}에 게시되었습니다!")

    def _on_post_error(self, platform_name, error):
        """게시 실패 콜백"""
        self.status_label.configure(text=f"{platform_name} 게시 실패")
        self.x_post_btn.configure(state="normal")
        self.ig_post_btn.configure(state="normal")
        messagebox.showerror("게시 실패", f"{platform_name} 게시 중 오류:\n{error}")

    # ===== 설정 =====

    def open_settings(self):
        """설정 다이얼로그 열기"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("소셜미디어 설정")
        dialog.geometry("450x520")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # X 설정 섹션
        x_frame = ctk.CTkFrame(dialog)
        x_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(x_frame, text="X (Twitter) API", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=15, pady=(15, 10), anchor="w")

        x_cfg = self.config.get("x", {})
        x_entries = {}
        for label, key in [("API Key", "api_key"), ("API Secret", "api_secret"),
                           ("Access Token", "access_token"), ("Access Token Secret", "access_token_secret")]:
            row = ctk.CTkFrame(x_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=label, width=140, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, width=250, show="*")
            entry.pack(side="left", fill="x", expand=True)
            entry.insert(0, x_cfg.get(key, ""))
            x_entries[key] = entry

        # 인스타그램 설정 섹션
        ig_frame = ctk.CTkFrame(dialog)
        ig_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(ig_frame, text="Instagram", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=15, pady=(15, 10), anchor="w")

        ig_cfg = self.config.get("instagram", {})
        ig_entries = {}
        for label, key, show in [("Username", "username", ""), ("Password", "password", "*")]:
            row = ctk.CTkFrame(ig_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=label, width=140, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, width=250, show=show if show else "")
            entry.pack(side="left", fill="x", expand=True)
            entry.insert(0, ig_cfg.get(key, ""))
            ig_entries[key] = entry

        ctk.CTkLabel(ig_frame, text="").pack(pady=5)

        # 버튼 영역
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        def do_save():
            self.config["x"] = {key: entry.get().strip() for key, entry in x_entries.items()}
            self.config["instagram"] = {key: entry.get().strip() for key, entry in ig_entries.items()}
            save_config(self.config)
            self.status_label.configure(text="설정이 저장되었습니다.")
            dialog.destroy()

        def do_test_x():
            if not all(e.get().strip() for e in x_entries.values()):
                messagebox.showwarning("알림", "모든 X API 키를 입력하세요.", parent=dialog)
                return
            try:
                poster = XPoster(
                    x_entries["api_key"].get().strip(),
                    x_entries["api_secret"].get().strip(),
                    x_entries["access_token"].get().strip(),
                    x_entries["access_token_secret"].get().strip(),
                )
                if poster.test_connection():
                    messagebox.showinfo("성공", "X 연결 테스트 성공!", parent=dialog)
                else:
                    messagebox.showerror("실패", "X 연결 테스트 실패.", parent=dialog)
            except Exception as e:
                messagebox.showerror("오류", f"X 연결 오류:\n{e}", parent=dialog)

        def do_test_ig():
            if not all(e.get().strip() for e in ig_entries.values()):
                messagebox.showwarning("알림", "인스타그램 계정 정보를 입력하세요.", parent=dialog)
                return
            try:
                poster = InstagramPoster(
                    ig_entries["username"].get().strip(),
                    ig_entries["password"].get().strip(),
                )
                if poster.test_connection():
                    messagebox.showinfo("성공", "인스타그램 로그인 테스트 성공!", parent=dialog)
                else:
                    messagebox.showerror("실패", "인스타그램 로그인 테스트 실패.", parent=dialog)
            except Exception as e:
                messagebox.showerror("오류", f"인스타그램 로그인 오류:\n{e}", parent=dialog)

        ctk.CTkButton(btn_frame, text="X 연결 테스트", command=do_test_x, width=120, fg_color="#1DA1F2").pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="인스타 연결 테스트", command=do_test_ig, width=130, fg_color="#E1306C").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="저장", command=do_save, width=80).pack(side="right", padx=(5, 0))
        ctk.CTkButton(btn_frame, text="취소", command=dialog.destroy, width=80, fg_color="gray40").pack(side="right", padx=5)

    def show_error(self, message):
        """에러 표시"""
        self.status_label.configure(text=f"오류: {message}")
        messagebox.showerror("오류", message)


if __name__ == "__main__":
    app = BostonKoreaApp()
    app.mainloop()
