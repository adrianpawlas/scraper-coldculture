# Cold Culture Scraper

Automated scraper for Cold Culture fashion store with embeddings and Supabase integration.

## Features

- Scrapes 4 categories: all-products, accessories, sneakers, last-units (sale)
- Infinite scroll handling for dynamic product loading
- Image embeddings using `google/siglip-base-patch16-384` (768-dim)
- Text embeddings from product info
- Auto-imports to Supabase database
- Daily automated runs at midnight UTC
- Manual trigger available

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. Set up GitHub secrets (for automation):
   - Go to your repository Settings > Secrets > New repository secret
   - Add `SUPABASE_URL`: `https://yqawmzggcgpeyaaynrjk.supabase.co`
   - Add `SUPABASE_KEY`: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxYXdtemdnY2dwZXlhYXlucmprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTAxMDkyNiwiZXhwIjoyMDcwNTg2OTI2fQ.XtLpxausFriraFJeX27ZzsdQsFv3uQKXBBggoz6P4D4`

4. For local running, create a `.env` file:
   ```
   SUPABASE_URL=https://yqawmzggcgpeyaaynrjk.supabase.co
   SUPABASE_KEY=your_anon_key_here
   ```

## Usage

### Full pipeline (recommended)
```bash
python -m src.main
```

### Step by step
```bash
python step1_scrape.py      # Scrapes products
python step2_embeddings.py # Adds embeddings
python step3_import.py     # Imports to Supabase
```

## Automation

The scraper runs automatically:
- **Daily at midnight UTC** via GitHub Actions
- **Manually** via GitHub Actions workflow dispatch

### To trigger manually:
1. Go to Actions tab in GitHub
2. Select "Cold Culture Scraper"
3. Click "Run workflow"

## Output

- `scraped_products.json` - Raw product data
- `scraped_products_with_embeddings.json` - Products with embeddings

## Supabase Schema

The scraper imports to the `products` table with these fields:
- `id`, `source`, `product_url`, `image_url`, `brand`, `title`, `description`
- `category`, `gender`, `metadata`, `size`, `second_hand`, `country`
- `price`, `sale`, `additional_images`, `image_embedding`, `info_embedding`
- `created_at`
