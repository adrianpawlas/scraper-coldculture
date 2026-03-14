import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.supabase_importer import SupabaseImporter

INPUT_FILE = "scraped_products_with_embeddings.json"

def main():
    print("Loading products with embeddings...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"Loaded {len(products)} products")
    
    print("\nConnecting to Supabase...")
    importer = SupabaseImporter()
    
    print("Inserting products...")
    success, failed = importer.insert_products_batch(products)
    
    print(f"\nResults:")
    print(f"  Success: {success}")
    print(f"  Failed: {len(failed)}")
    
    if failed:
        print("\nFailed products:")
        for pid, err in failed[:10]:
            print(f"  - {pid}: {err[:100]}")

if __name__ == "__main__":
    main()
