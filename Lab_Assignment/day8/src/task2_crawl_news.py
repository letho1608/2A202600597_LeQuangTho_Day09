"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# Danh sách URL bài báo về nghệ sĩ liên quan tới ma tuý cuối năm 2024 - 2026
ARTICLE_URLS = [
    "https://tuoitre.vn/ca-si-chi-dan-nguoi-mau-an-tay-co-tien-truc-phuong-to-chuc-su-dung-ma-tuy-ra-sao-20241114085434125.htm",
    "https://plo.vn/truy-to-ca-si-chi-dan-nguoi-mau-an-tay-va-truc-phuong-post818045.html",
    "https://vov.vn/phap-luat/khoi-to-ca-si-chi-dan-nguoi-mau-andrea-ve-hanh-vi-to-chuc-su-dung-ma-tuy-post1135241.vov",
    "https://thanhnien.vn/ca-si-chi-dan-bi-tam-giu-vi-nghi-lien-quan-den-ma-tuy-185241111111327157.htm",
    "https://kenh14.vn/chi-dan-va-an-tay-bi-tam-giu-vi-lien-quan-den-ma-tuy-20241111112447936.chn"
]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài báo sử dụng Crawl4AI.
    """
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return {
            "url": url,
            "title": url.split("/")[-1].replace(".htm", "").replace(".html", "").replace("-", " "),
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": result.markdown,
        }


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        article = await crawl_article(url)

        # Lưu file JSON
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm bài báo trên VnExpress, Tuổi Trẻ, Thanh Niên, ...")
    else:
        asyncio.run(crawl_all())
