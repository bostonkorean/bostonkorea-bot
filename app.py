#!/usr/bin/env python3
"""
보스톤코리아 소셜미디어 포스팅 봇 - 데스크탑 앱
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
from bostonkorea_bot import BostonKoreaBot

# 테마 설정
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BostonKoreaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.bot = BostonKoreaBot()
        self.articles = []
        self.current_article = None

        # 윈도우 설정
        self.title("보스톤코리아 소셜미디어 봇")
        self.geometry("900x700")
        self.minsize(800, 600)

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
        self.refresh_btn.grid(row=0, column=3, padx=15, pady=15)

    def _create_main_content(self):
        """메인 컨텐츠 영역"""
        main = ctk.CTkFrame(self)
        main.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # 왼쪽: 기사 목록
        self._create_article_list(main)

        # 오른쪽: 결과 패널
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
        """결과 패널"""
        result_frame = ctk.CTkFrame(parent)
        result_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_rowconfigure(3, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # X 섹션
        x_header_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
        x_header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        x_header_frame.grid_columnconfigure(0, weight=1)

        x_label = ctk.CTkLabel(
            x_header_frame,
            text="X (트위터)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        x_label.grid(row=0, column=0, sticky="w")

        self.x_copy_btn = ctk.CTkButton(
            x_header_frame,
            text="복사",
            command=lambda: self.copy_to_clipboard("x"),
            width=60,
            height=28
        )
        self.x_copy_btn.grid(row=0, column=1)

        self.x_textbox = ctk.CTkTextbox(result_frame, height=150)
        self.x_textbox.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 10))

        # 인스타그램 섹션
        ig_header_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
        ig_header_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(10, 5))
        ig_header_frame.grid_columnconfigure(0, weight=1)

        ig_label = ctk.CTkLabel(
            ig_header_frame,
            text="인스타그램",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        ig_label.grid(row=0, column=0, sticky="w")

        self.ig_copy_btn = ctk.CTkButton(
            ig_header_frame,
            text="복사",
            command=lambda: self.copy_to_clipboard("instagram"),
            width=60,
            height=28
        )
        self.ig_copy_btn.grid(row=0, column=1)

        self.ig_textbox = ctk.CTkTextbox(result_frame, height=200)
        self.ig_textbox.grid(row=3, column=0, sticky="nsew", padx=15, pady=(0, 15))

        # 초기 안내 메시지
        self.x_textbox.insert("1.0", "← 왼쪽에서 기사를 선택하세요")
        self.ig_textbox.insert("1.0", "← 왼쪽에서 기사를 선택하세요")
        self.x_textbox.configure(state="disabled")
        self.ig_textbox.configure(state="disabled")

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

        # 기존 위젯 제거
        for widget in self.article_scroll.winfo_children():
            widget.destroy()

        if not articles:
            no_data = ctk.CTkLabel(
                self.article_scroll,
                text="기사가 없습니다",
                font=ctk.CTkFont(size=14)
            )
            no_data.grid(row=0, column=0, pady=50)
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

        # 제목
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

        # 카테고리 태그
        if article.get('category'):
            cat_label = ctk.CTkLabel(
                card,
                text=article['category'],
                font=ctk.CTkFont(size=11),
                fg_color=("gray80", "gray25"),
                corner_radius=4
            )
            cat_label.grid(row=0, column=1, padx=10, pady=10)

    def select_article(self, article):
        """기사 선택 및 변환"""
        self.status_label.configure(text="기사를 변환하는 중...")
        self.current_article = article

        def process():
            try:
                full_article = self.bot.fetch_article(article['url'])
                result = self.bot.format_for_both(full_article)
                self.after(0, lambda: self.display_result(result))
            except Exception as e:
                self.after(0, lambda: self.show_error(str(e)))

        threading.Thread(target=process, daemon=True).start()

    def display_result(self, result):
        """결과 표시"""
        # X 텍스트
        self.x_textbox.configure(state="normal")
        self.x_textbox.delete("1.0", "end")
        self.x_textbox.insert("1.0", result['x'])

        # 인스타그램 텍스트
        self.ig_textbox.configure(state="normal")
        self.ig_textbox.delete("1.0", "end")
        self.ig_textbox.insert("1.0", result['instagram'])

        self.status_label.configure(text="변환 완료!")

    def copy_to_clipboard(self, platform):
        """클립보드에 복사"""
        if platform == "x":
            text = self.x_textbox.get("1.0", "end-1c")
        else:
            text = self.ig_textbox.get("1.0", "end-1c")

        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_label.configure(text=f"{'X' if platform == 'x' else '인스타그램'}용 텍스트 복사됨!")

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

    def show_error(self, message):
        """에러 표시"""
        self.status_label.configure(text=f"오류: {message}")
        messagebox.showerror("오류", message)


if __name__ == "__main__":
    app = BostonKoreaApp()
    app.mainloop()
