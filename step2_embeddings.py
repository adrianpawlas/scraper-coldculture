import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.embeddings import EmbeddingGenerator

INPUT_FILE = "scraped_products.json"
OUTPUT_FILE = "scraped_products_with_embeddings.json"

def main():
    print("Loading products...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"Loaded {len(products)} products")
    
    print("\nInitializing embedding generator...")
    embedding_gen = EmbeddingGenerator()
    
    for i, product in enumerate(products):
        print(f"\nProcessing {i+1}/{len(products)}: {product.get('title', 'unknown')[:40]}...")
        
        image_url = product.get('image_url')
        if image_url:
            print(f"  Generating image embedding from: {image_url[:50]}...")
            img_emb = embedding_gen.generate_image_embedding(image_url)
            product['image_embedding'] = img_emb
            if img_emb:
                print(f"  Image embedding: {len(img_emb)} dims")
        
        print(f"  Generating info embedding...")
        info_emb = embedding_gen.generate_info_embedding(product)
        product['info_embedding'] = info_emb
        if info_emb:
            print(f"  Info embedding: {len(info_emb)} dims")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
