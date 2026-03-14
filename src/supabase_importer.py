import json
import os
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://yqawmzggcgpeyaaynrjk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxYXdtemdnY2dwZXlhYXlucmprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTAxMDkyNiwiZXhwIjoyMDcwNTg2OTI2fQ.XtLpxausFriraFJeX27ZzsdQsFv3uQKXBBggoz6P4D4")

class SupabaseImporter:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Connected to Supabase!")
    
    def insert_product(self, product_data: Dict[str, Any]) -> bool:
        """Insert a single product into the database"""
        try:
            data = {k: v for k, v in product_data.items() if v is not None}
            
            result = self.client.table('products').upsert(
                data,
                on_conflict='source,product_url'
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error inserting product: {e}")
            return False
    
    def insert_products_batch(self, products: List[Dict[str, Any]]) -> tuple:
        """Insert multiple products at once"""
        success_count = 0
        failed = []
        
        for product in products:
            try:
                data = {k: v for k, v in product.items() if v is not None}
                
                self.client.table('products').upsert(
                    data,
                    on_conflict='source,product_url'
                ).execute()
                
                success_count += 1
            except Exception as e:
                failed.append((product.get('id', 'unknown'), str(e)))
        
        return success_count, failed
    
    def check_existing_products(self, source: str) -> List[str]:
        """Get list of existing product IDs for a source"""
        try:
            result = self.client.table('products').select('id').eq('source', source).execute()
            return [r['id'] for r in result.data]
        except Exception as e:
            print(f"Error checking existing products: {e}")
            return []

async def main():
    """Test the Supabase connection"""
    importer = SupabaseImporter()
    
    test_product = {
        "id": "test-123",
        "source": "scraper-test",
        "product_url": "https://test.com/product",
        "brand": "Test Brand",
        "title": "Test Product",
        "image_url": "https://test.com/image.jpg",
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    print("Supabase importer ready!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
