import os
import json
import asyncio
import aiohttp
import httpx
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from playwright.async_api import async_playwright

SUPABASE_URL = "https://yqawmzggcgpeyaaynrjk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxYXdtemdnY2dwZXlhYXlucmprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTAxMDkyNiwiZXhwIjoyMDcwNTg2OTI2fQ.XtLpxausFriraFJeX27ZzsdQsFv3uQKXBBggoz6P4D4"

CATEGORIES = {
    "all-products": "https://coldcultureworldwide.com/collections/all-products",
    "accessories": "https://coldcultureworldwide.com/collections/accessories",
    "sneakers": "https://coldcultureworldwide.com/collections/sneakers",
    "last-units": "https://coldcultureworldwide.com/collections/last-units"
}

BRAND = "Cold Culture"
SOURCE = "scraper-coldculture"

@dataclass
class Product:
    id: str
    source: str
    product_url: str
    image_url: str
    brand: str
    title: str
    description: Optional[str]
    category: Optional[str]
    gender: Optional[str]
    metadata: Optional[str]
    size: Optional[str]
    second_hand: bool
    image_embedding: Optional[list]
    country: Optional[str]
    compressed_image_url: Optional[str]
    tags: Optional[list]
    other: Optional[str]
    price: Optional[str]
    sale: Optional[str]
    additional_images: Optional[str]
    info_embedding: Optional[list]
    created_at: str
    
    def to_dict(self):
        return asdict(self)

async def scroll_page(page, max_scrolls=50):
    """Scroll page until no more products load"""
    products_before = 0
    products_after = 0
    scroll_count = 0
    no_change_count = 0
    
    while scroll_count < max_scrolls:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        
        products_after = await page.locator('.product-card, .product-item, [data-product-id], .grid-view-item, .card').count()
        
        if products_before == products_after:
            no_change_count += 1
            if no_change_count >= 3:
                break
        else:
            no_change_count = 0
            
        products_before = products_after
        scroll_count += 1
        print(f"Scroll {scroll_count}: Found {products_after} products")
    
    return products_after

async def get_product_links_from_category(category_url: str, is_sale: bool = False) -> list:
    """Get all product URLs from a category page with infinite scroll"""
    product_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Loading category: {category_url}")
        await page.goto(category_url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        
        await scroll_page(page)
        
        links = await page.locator('a[href*="/products/"]').all()
        for link in links:
            href = await link.get_attribute('href')
            if href and '/products/' in href and href not in product_urls:
                full_url = href if href.startswith('http') else f"https://coldcultureworldwide.com{href}"
                product_urls.append(full_url)
        
        await browser.close()
    
    print(f"Found {len(product_urls)} products in {category_url}")
    return product_urls

async def extract_price_with_currency(price_text: str) -> str:
    """Extract price and currency, format as requested"""
    if not price_text:
        return ""
    
    import re
    prices = []
    
    patterns = [
        r'([\d,]+\.?\d*)\s*(USD|EUR|GBP|PLN|CZK|SEK|NOK|DKK|CHF|CAD|AUD|JPY)',
        r'([\d,]+\.?\d*)\s*\$',
        r'€\s*([\d,]+\.?\d*)',
        r'£\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, price_text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                num = match[0].replace(',', '')
                curr = match[1].upper() if len(match) > 1 else 'USD'
                prices.append(f"{num}{curr}")
            else:
                num = match.replace(',', '')
                prices.append(f"{num}USD")
    
    if not prices:
        numbers = re.findall(r'[\d,]+\.?\d*', price_text)
        for num in numbers:
            prices.append(f"{num}USD")
    
    return ",".join(prices) if prices else price_text

async def scrape_product(url: str, category: str, is_sale: bool = False) -> Optional[Product]:
    """Scrape individual product page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            title = ""
            try:
                title = await page.locator('h1.product-title, h1.title, h1').first.text_content(timeout=5000) or ""
                title = title.strip()
            except:
                pass
            
            if not title:
                try:
                    title = await page.title() or ""
                except:
                    pass
            
            description = ""
            try:
                desc_elem = page.locator('.product-description, .description, [itemprop="description"], .rte').first
                description = await desc_elem.text_content(timeout=3000) or ""
            except:
                pass
            
            price_text = ""
            try:
                price_elem = page.locator('.price-item--regular, .product-price, .price .money, [itemprop="price"], .price__sale .price-item--regular').first
                price_text = await price_elem.text_content(timeout=3000) or ""
            except:
                try:
                    price_elem = page.locator('.price, .product-price').first
                    price_text = await price_elem.text_content(timeout=3000) or ""
                except:
                    pass
            
            sale_text = ""
            if is_sale:
                sale_text = price_text
            
            image_url = ""
            try:
                img = page.locator('.product-featured-image, .featured-image img, [itemprop="image"], .product__media img').first
                image_url = await img.get_attribute('src') or await img.get_attribute('data-src') or ""
            except:
                try:
                    img = page.locator('.product-image img').first
                    image_url = await img.get_attribute('src') or await img.get_attribute('data-src') or ""
                except:
                    pass
            
            if not image_url:
                try:
                    img = page.locator('img[alt*="product"]').first
                    image_url = await img.get_attribute('src') or ""
                except:
                    pass
            
            additional_images_list = []
            try:
                thumbs = await page.locator('.product-thumbnail img, .thumbnails img, .product__media--thumbnail img').all()
                for thumb in thumbs[:5]:
                    src = await thumb.get_attribute('src') or await thumb.get_attribute('data-src')
                    if src and src != image_url and 'placeholder' not in src.lower() and src not in additional_images_list:
                        additional_images_list.append(src)
            except:
                pass
            
            additional_images = ", ".join(additional_images_list) if additional_images_list else None
            
            gender = "man"
            if any(word in category.lower() for word in ['woman', 'women', 'dress', 'skirt', 'blouse']):
                gender = "woman"
            
            categories = category.replace('-', ' ').title()
            
            metadata = json.dumps({
                "title": title,
                "description": description,
                "price": price_text,
                "sale": sale_text,
                "category": category,
                "gender": gender,
                "scraped_at": datetime.now().isoformat()
            })
            
            product_id = url.split('/products/')[-1].split('?')[0] if '/products/' in url else url.split('/')[-1]
            
            price = await extract_price_with_currency(price_text)
            sale = await extract_price_with_currency(sale_text) if sale_text else None
            
            await browser.close()
            
            return Product(
                id=f"{SOURCE}_{product_id}",
                source=SOURCE,
                product_url=url,
                image_url=image_url,
                brand=BRAND,
                title=title,
                description=description[:500] if description else None,
                category=categories,
                gender=gender,
                metadata=metadata,
                size=None,
                second_hand=False,
                image_embedding=None,
                country=None,
                compressed_image_url=None,
                tags=None,
                other=None,
                price=price,
                sale=sale,
                additional_images=additional_images,
                info_embedding=None,
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            await browser.close()
            return None

async def main():
    print("Starting Cold Culture scraper...")
    
    all_product_urls = {}
    
    for cat_key, cat_url in CATEGORIES.items():
        is_sale = cat_key == "last-units"
        urls = await get_product_links_from_category(cat_url, is_sale)
        all_product_urls[cat_key] = {"urls": urls, "is_sale": is_sale}
    
    print(f"\nTotal unique products to scrape: {sum(len(v['urls']) for v in all_product_urls.values())}")
    
    all_products = []
    
    for cat_key, data in all_product_urls.items():
        print(f"\nScraping category: {cat_key}")
        for url in data['urls']:
            product = await scrape_product(url, cat_key, data['is_sale'])
            if product:
                all_products.append(product)
                print(f"  Scraped: {product.title[:50]}...")
    
    print(f"\nTotal products scraped: {len(all_products)}")
    
    with open('scraped_products.json', 'w', encoding='utf-8') as f:
        json.dump([p.to_dict() for p in all_products], f, indent=2, ensure_ascii=False)
    
    print("Products saved to scraped_products.json")

if __name__ == "__main__":
    asyncio.run(main())
