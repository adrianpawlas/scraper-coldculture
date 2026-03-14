import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import CATEGORIES, get_product_links_from_category, scrape_product

OUTPUT_FILE = "scraped_products.json"

async def main():
    print("Step 1: Scraping product URLs...")
    
    all_product_urls = {}
    
    for cat_key, cat_url in CATEGORIES.items():
        is_sale = cat_key == "last-units"
        print(f"\n  {cat_key}: {cat_url}")
        urls = await get_product_links_from_category(cat_url, is_sale)
        all_product_urls[cat_key] = {"urls": urls, "is_sale": is_sale}
        print(f"  Found {len(urls)} products")
    
    print("\nStep 2: Scraping product details...")
    all_products = []
    seen_urls = set()
    
    for cat_key, data in all_product_urls.items():
        print(f"\n  Category: {cat_key}")
        count = 0
        for url in data['urls']:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            product = await scrape_product(url, cat_key, data['is_sale'])
            if product:
                all_products.append(product)
                count += 1
                print(f"    {count}. {product.title[:50]}...")
        
        print(f"  Total: {count}")
    
    print(f"\nTotal products: {len(all_products)}")
    
    products_data = [p.to_dict() for p in all_products]
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(products_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
