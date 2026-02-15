#!/usr/bin/env python3
"""
보스톤코리아 기사 → 소셜미디어 포스팅 봇
인스타그램과 X(트위터)용 텍스트를 자동 생성합니다.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import re
import sys
import pyperclip

class BostonKoreaBot:
    BASE_URL = 'https://www.bostonkorea.com'

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch_latest_articles(self, category: str = None, limit: int = 15) -> list:
        """최신 기사 목록 가져오기"""
        if category:
            url = f"{self.BASE_URL}/bbs/board.php?bo_table=news&sca={category}"
        else:
            url = f"{self.BASE_URL}/bbs/board.php?bo_table=news"

        response = requests.get(url, headers=self.headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        articles = []

        # webzineList 구조에서 기사 추출 (메인 콘텐츠 영역만)
        # 사이드바(.hot_issue 등) 제외
        main_content = soup.select_one('#bo_list, .board_list, #container')
        if main_content:
            items = main_content.select('.webzineList > ul > li')
        else:
            items = soup.select('.webzineList > ul > li')

        for item in items[:limit]:
            link = item.select_one('a')
            if not link:
                continue

            href = link.get('href', '')
            if not href or '/news/' not in href:
                continue

            # 제목 추출 (strong 태그에서)
            title_elem = item.select_one('.bo_tit strong')
            if title_elem:
                title = title_elem.get_text(strip=True)
            else:
                # 대체: bo_tit에서 전체 텍스트
                tit_elem = item.select_one('.bo_tit')
                title = tit_elem.get_text(strip=True) if tit_elem else ''

            # 제목 앞 숫자 제거 (예: "1.제목" → "제목")
            title = re.sub(r'^\d+\.', '', title).strip()

            if not title or len(title) < 5:
                continue

            full_url = href if href.startswith('http') else self.BASE_URL + href

            # 카테고리 추출
            cat_elem = item.select_one('.bo_tit em')
            category_text = ''
            if cat_elem:
                # em 태그에서 카테고리 정보가 있으면 추출
                em_text = cat_elem.get_text(strip=True)
                # 본문 요약이 아닌 짧은 카테고리만
                if len(em_text) < 20:
                    category_text = em_text

            articles.append({
                'title': title[:55] + '...' if len(title) > 55 else title,
                'url': full_url,
                'category': category_text
            })

        # webzineList가 없으면 대체 방식
        if not articles and not category:
            links = soup.select('a[href*="/news/"]')
            seen_urls = set()
            for link in links:
                href = link.get('href', '')
                title_elem = link.select_one('strong') or link
                title = title_elem.get_text(strip=True)

                if '/news/' in href and href not in seen_urls and title and len(title) > 10:
                    full_url = href if href.startswith('http') else self.BASE_URL + href
                    seen_urls.add(href)
                    articles.append({
                        'title': title[:55] + '...' if len(title) > 55 else title,
                        'url': full_url,
                        'category': ''
                    })
                    if len(articles) >= limit:
                        break

        return articles

    def get_categories(self) -> dict:
        """사용 가능한 카테고리 목록"""
        return {
            '전체': '',
            '미국': '미국',
            '한국': '한국',
            '경제': '경제',
            '비즈니스': '비즈니스',
            '미국주식': '미국주식',
            '스포츠': '스포츠',
            '교육유학': '교육유학',
            '칼럼': '칼럼',
        }

    def fetch_article(self, url: str) -> dict:
        """기사 URL에서 정보 추출"""
        response = requests.get(url, headers=self.headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 제목 추출
        title_elem = soup.select_one('#bo_v_title .bo_v_tit, h2.bo_v_tit')
        title = title_elem.get_text(strip=True) if title_elem else "제목 없음"

        # 본문 추출
        content_elem = soup.select_one('#bo_v_con')
        if content_elem:
            # 스크립트, 스타일 제거
            for tag in content_elem.find_all(['script', 'style', 'iframe']):
                tag.decompose()
            content = content_elem.get_text(separator='\n', strip=True)
            # 여러 줄바꿈을 하나로
            content = re.sub(r'\n{3,}', '\n\n', content)
        else:
            content = ""

        # 이미지 추출
        img_elem = soup.select_one('#bo_v_img img, #bo_v_con img')
        image_url = img_elem.get('src') if img_elem else None

        # 날짜 추출
        date_elem = soup.select_one('.bo_v_info')
        date_text = ""
        if date_elem:
            date_match = re.search(r'(\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2})', date_elem.get_text())
            if date_match:
                date_text = date_match.group(1)

        # 카테고리 추출
        category = ""
        breadcrumb = soup.select('.bo_v_cate a, .bo_tit em')
        if breadcrumb:
            category = breadcrumb[-1].get_text(strip=True)

        return {
            'url': url,
            'title': title,
            'content': content[:2000],  # 처음 2000자만
            'image_url': image_url,
            'date': date_text,
            'category': category
        }

    def summarize_content(self, content: str, max_length: int = 200) -> str:
        """본문 요약 (첫 문장들 추출)"""
        sentences = re.split(r'[.。]\s*', content)
        summary = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(summary) + len(sentence) + 2 > max_length:
                break
            summary += sentence + ". "
        return summary.strip()

    def generate_hashtags(self, title: str, category: str) -> str:
        """해시태그 생성"""
        tags = ['#보스톤코리아', '#보스톤', '#Boston', '#미국뉴스']

        # 카테고리별 태그 추가
        category_tags = {
            '경제': ['#경제', '#비즈니스'],
            '비즈니스': ['#비즈니스', '#경제뉴스'],
            '미국주식': ['#미국주식', '#주식', '#투자'],
            '스포츠': ['#스포츠', '#MLB', '#NBA'],
            '한국': ['#한국뉴스', '#Korea'],
            '교육': ['#교육', '#유학'],
            '부동산': ['#부동산', '#미국부동산'],
        }

        for key, extra_tags in category_tags.items():
            if key in category:
                tags.extend(extra_tags)
                break

        return ' '.join(tags[:8])  # 최대 8개

    def format_for_x(self, article: dict) -> str:
        """X(트위터)용 포맷 생성 (280자 제한)"""
        title = article['title']
        url = article['url']
        hashtags = self.generate_hashtags(title, article['category'])

        # URL은 약 23자로 계산 (t.co 단축)
        url_length = 23
        hashtag_length = len(hashtags)
        available = 280 - url_length - hashtag_length - 4  # 여유 공간

        if len(title) > available:
            title = title[:available-3] + "..."

        return f"{title}\n\n{url}\n\n{hashtags}"

    def format_for_instagram(self, article: dict) -> str:
        """인스타그램용 포맷 생성"""
        title = article['title']
        summary = self.summarize_content(article['content'], 300)
        hashtags = self.generate_hashtags(title, article['category'])

        # 인스타그램용 추가 해시태그
        extra_tags = '#뉴스 #미주한인 #재미교포 #한인커뮤니티 #보스톤한인'

        post = f"""📰 {title}

{summary}

👉 자세한 내용은 프로필 링크에서 확인하세요!

{hashtags}
{extra_tags}"""

        return post

    def format_for_both(self, article: dict) -> dict:
        """두 플랫폼용 포맷 모두 생성"""
        return {
            'x': self.format_for_x(article),
            'instagram': self.format_for_instagram(article),
            'image_url': article.get('image_url', '')
        }


def process_article(bot, url):
    """기사 처리 및 출력"""
    print("\n⏳ 기사를 가져오는 중...")
    article = bot.fetch_article(url)
    result = bot.format_for_both(article)

    print("\n" + "=" * 50)
    print("📌 기사 정보")
    print("=" * 50)
    print(f"제목: {article['title']}")
    print(f"카테고리: {article['category']}")
    print(f"날짜: {article['date']}")

    print("\n" + "-" * 50)
    print("🐦 X (트위터)용 텍스트:")
    print("-" * 50)
    print(result['x'])
    print(f"\n📏 글자 수: {len(result['x'])}자")

    print("\n" + "-" * 50)
    print("📸 인스타그램용 텍스트:")
    print("-" * 50)
    print(result['instagram'])

    if result['image_url']:
        print(f"\n🖼️  이미지 URL: {result['image_url']}")

    # 클립보드 복사 옵션
    print("\n" + "-" * 50)
    print("복사할 텍스트를 선택하세요:")
    print("1. X용 텍스트")
    print("2. 인스타그램용 텍스트")
    print("3. 건너뛰기")

    copy_choice = input("\n선택 (1-3): ").strip()

    if copy_choice == '1':
        try:
            pyperclip.copy(result['x'])
            print("✅ X용 텍스트가 클립보드에 복사되었습니다!")
        except:
            print("⚠️  클립보드 복사 실패. 텍스트를 수동으로 복사하세요.")
    elif copy_choice == '2':
        try:
            pyperclip.copy(result['instagram'])
            print("✅ 인스타그램용 텍스트가 클립보드에 복사되었습니다!")
        except:
            print("⚠️  클립보드 복사 실패. 텍스트를 수동으로 복사하세요.")


def show_article_list(bot):
    """최신 기사 목록 표시 및 선택"""
    categories = bot.get_categories()

    print("\n" + "=" * 50)
    print("📂 카테고리 선택")
    print("=" * 50)

    cat_list = list(categories.keys())
    for i, cat in enumerate(cat_list, 1):
        print(f"{i}. {cat}")

    cat_choice = input("\n카테고리 선택 (기본: 전체): ").strip()

    try:
        cat_idx = int(cat_choice) - 1 if cat_choice else 0
        selected_cat = categories[cat_list[cat_idx]]
    except:
        selected_cat = ''

    print("\n⏳ 최신 기사를 가져오는 중...")
    articles = bot.fetch_latest_articles(category=selected_cat, limit=15)

    if not articles:
        print("❌ 기사를 찾을 수 없습니다.")
        return None

    print("\n" + "=" * 50)
    print(f"📰 최신 기사 목록 ({len(articles)}개)")
    print("=" * 50)

    for i, article in enumerate(articles, 1):
        cat_tag = f"[{article['category']}] " if article['category'] else ""
        print(f"{i:2}. {cat_tag}{article['title']}")

    print("\n0. 메인 메뉴로 돌아가기")

    article_choice = input("\n기사 번호 선택: ").strip()

    try:
        idx = int(article_choice)
        if idx == 0:
            return None
        if 1 <= idx <= len(articles):
            return articles[idx - 1]['url']
    except:
        pass

    print("❌ 잘못된 선택입니다.")
    return None


def main():
    bot = BostonKoreaBot()

    print("=" * 50)
    print("🗞️  보스톤코리아 소셜미디어 포스팅 봇")
    print("=" * 50)

    while True:
        print("\n옵션을 선택하세요:")
        print("1. 최신 기사 목록 보기")
        print("2. 기사 URL 직접 입력")
        print("3. 종료")

        choice = input("\n선택 (1-3): ").strip()

        if choice == '3':
            print("👋 종료합니다.")
            break

        if choice == '1':
            url = show_article_list(bot)
            if url:
                try:
                    process_article(bot, url)
                except Exception as e:
                    print(f"❌ 오류 발생: {e}")
            continue

        if choice != '2':
            print("❌ 잘못된 선택입니다.")
            continue

        url = input("\n기사 URL을 입력하세요: ").strip()

        if not url.startswith('http'):
            print("❌ 올바른 URL을 입력하세요.")
            continue

        try:
            process_article(bot, url)
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            continue


if __name__ == "__main__":
    main()
