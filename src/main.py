import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import CATEGORIES, BRAND, SOURCE, get_product_links_from_category, scrape_product
from embeddings import EmbeddingGenerator
from supabase_importer import SupabaseImporter

OUTPUT_FILE = "scraped_products.json"

async def main():
    print("=" * 60)
    print("Cold Culture Scraper - Full Pipeline")
    print("=" * 60)
    
    all_product_urls = {}
    
    print("\n[1/4] Scraping product URLs from categories...")
    for cat_key, cat_url in CATEGORIES.items():
        is_sale = cat_key == "last-units"
        print(f"\n  Category: {cat_key}")
        urls = await get_product_links_from_category(cat_url, is_sale)
        all_product_urls[cat_key] = {"urls": urls, "is_sale": is_sale}
        print(f"  Found {len(urls)} products")
    
    print(f"\n  Total: {sum(len(v['urls']) for v in all_product_urls.values())} products")
    
    print("\n[2/4] Scraping product details...")
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
                if count % 10 == 0:
                    print(f"    Scraped {count} products...")
        
        print(f"    Total scraped: {count}")
    
    print(f"\n  Total unique products: {len(all_products)}")
    
    print("\n[3/4] Generating embeddings...")
    embedding_gen = EmbeddingGenerator()
    
    for i, product in enumerate(all_products):
        print(f"  Processing {i+1}/{len(all_products)}: {product.title[:40]}...")
        
        if product.image_url:
            img_emb = embedding_gen.generate_image_embedding(product.image_url)
            product.image_embedding = img_emb
        
        info_emb = embedding_gen.generate_info_embedding(product.to_dict())
        product.info_embedding = info_emb
    
    print("\n[4/4] Importing to Supabase...")
    importer = SupabaseImporter()
    
    products_data = [p.to_dict() for p in all_products]
    
    success, failed = importer.insert_products_batch(products_data)
    
    print(f"\n  Success: {success}")
    print(f"  Failed: {len(failed)}")
    
    if failed:
        for pid, err in failed[:5]:
            print(f"    - {pid}: {err}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(products_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n  Saved to {OUTPUT_FILE}")
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
