import os
import torch
from sentence_transformers import SentenceTransformer

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(
    BASE_DIR,
    "..",
    "models",
    "fine_tuned_model",
    "final_model"
)

# Global config so other modules can access paths
CONFIG = {
    "DEVICE": DEVICE,
    "MODEL_PATH": MODEL_PATH,
    "BATCH_SIZE": 16
}

model = None

def initialize_model():
    """Load model only once and return instance"""
    global model
    
    if model is not None:
        return model

    print("⏳ Loading OptiRAG Embedding Model...")
    model = SentenceTransformer(MODEL_PATH, device=DEVICE)
    print("🚀 Model loaded successfully!")
    
    return model

# 🔥 Wrapper needed for dynamic_pipeline.py
def load_finetuned_model():
    """Wrapper for backward compatibility"""
    return initialize_model()
