import torch
import numpy as np
from transformers import AutoProcessor, AutoModel
from PIL import Image
import httpx
import asyncio
from io import BytesIO
from typing import Optional, List

MODEL_NAME = "google/siglip-base-patch16-384"
EMBEDDING_DIM = 768

class EmbeddingGenerator:
    def __init__(self):
        print(f"Loading SigLIP model: {MODEL_NAME}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        self.processor = AutoProcessor.from_pretrained(MODEL_NAME)
        self.model = AutoModel.from_pretrained(MODEL_NAME)
        self.model.to(self.device)
        self.model.eval()
        print("Model loaded successfully!")
    
    def generate_image_embedding(self, image_url: str) -> Optional[List[float]]:
        """Generate 768-dim embedding from image URL"""
        try:
            response = httpx.get(image_url, timeout=30)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content)).convert('RGB')
            
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)
                if hasattr(outputs, 'pooler_output'):
                    embedding = outputs.pooler_output
                else:
                    embedding = outputs.last_hidden_state[:, 0]
            
            embedding = embedding.cpu().numpy()[0].tolist()
            return embedding
            
        except Exception as e:
            print(f"Error generating image embedding for {image_url}: {e}")
            return None
    
    def generate_text_embedding(self, text: str) -> Optional[List[float]]:
        """Generate 768-dim embedding from text"""
        try:
            inputs = self.processor(text=text, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.get_text_features(**inputs)
                if hasattr(outputs, 'pooler_output'):
                    embedding = outputs.pooler_output
                else:
                    embedding = outputs.last_hidden_state[:, 0]
            
            embedding = embedding.cpu().numpy()[0].tolist()
            return embedding
            
        except Exception as e:
            print(f"Error generating text embedding: {e}")
            return None
    
    def generate_info_embedding(self, product_data: dict) -> Optional[List[float]]:
        """Generate embedding from all product info"""
        text_parts = [
            product_data.get('title', ''),
            product_data.get('brand', ''),
            product_data.get('description', ''),
            product_data.get('category', ''),
            product_data.get('gender', ''),
            product_data.get('price', ''),
            product_data.get('sale', ''),
            product_data.get('metadata', ''),
        ]
        
        text = " | ".join([str(part) for part in text_parts if part])
        return self.generate_text_embedding(text)

async def main():
    """Test the embedding generator"""
    generator = EmbeddingGenerator()
    
    test_text = "Cold Culture Sweater Blue"
    text_emb = generator.generate_text_embedding(test_text)
    print(f"Text embedding dim: {len(text_emb) if text_emb else 'Failed'}")
    
    print("\nEmbedding generator ready!")

if __name__ == "__main__":
    asyncio.run(main())
