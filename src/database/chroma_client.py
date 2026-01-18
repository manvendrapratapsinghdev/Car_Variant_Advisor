"""
ChromaDB client and collection management.
"""
import os as _os
# Silence noisy telemetry errors before importing chromadb
_os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.config import Settings
import re
from typing import Dict, List, Optional
import pandas as pd


def create_variant_id(make: str, model: str, variant: str) -> str:
    """Create unique variant ID."""
    make_clean = re.sub(r'[^a-z0-9]+', '_', str(make).lower().strip())
    model_clean = re.sub(r'[^a-z0-9]+', '_', str(model).lower().strip())
    variant_clean = re.sub(r'[^a-z0-9]+', '_', str(variant).lower().strip())
    return f"{make_clean}_{model_clean}_{variant_clean}"


class CarVariantDB:
    """
    ChromaDB client for car variant data.
    """
    
    def __init__(self, persist_directory: str = "./data/car_variants_db"):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_directory: Directory to store ChromaDB data
        """
        self.persist_directory = persist_directory
        
        # Create directory if it doesn't exist
        _os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Collection name
        self.collection_name = "car_variants"
        
        print(f"ChromaDB initialized at {persist_directory}")
    
    def create_collection(self, reset: bool = False):
        """
        Create or get the car variants collection.
        
        Args:
            reset: If True, delete existing collection and create new one
        """
        if reset:
            try:
                self.client.delete_collection(name=self.collection_name)
                print(f"Deleted existing collection: {self.collection_name}")
            except:
                pass
        
        try:
            # Use a simple custom embedding function to avoid SSL download issues
            # For MVP, we don't need actual embeddings as we're doing metadata filtering
            class DummyEmbeddingFunction:
                def __call__(self, input):
                    # Return simple dummy embeddings
                    if isinstance(input, list):
                        return [[0.0] * 384 for _ in input]
                    return [[0.0] * 384]
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Car variant specifications and features"},
                embedding_function=DummyEmbeddingFunction()
            )
            print(f"Collection '{self.collection_name}' ready")
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
    
    def ingest_data(self, df: pd.DataFrame, batch_size: int = 100):
        """
        Ingest variant data into ChromaDB.
        
        Args:
            df: DataFrame with variant data (from pickle file)
            batch_size: Number of documents to insert per batch
        """
        print(f"\n=== Ingesting {len(df)} variants ===")
        
        total_batches = (len(df) - 1) // batch_size + 1
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(df))
            
            batch_df = df.iloc[start_idx:end_idx]
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for idx, (_, row) in enumerate(batch_df.iterrows()):
                # ID - create from make/model/variant with counter for duplicates
                base_id = create_variant_id(row['Make'], row['Model'], row['Variant'])
                variant_id = f"{base_id}_{start_idx + idx}"  # Add row index to ensure uniqueness
                ids.append(variant_id)
                
                # Document (text for embedding - use feature summary)
                doc_text = str(row['feature_summary']) if pd.notna(row['feature_summary']) else f"{row['Make']} {row['Model']} {row['Variant']}"
                documents.append(doc_text)
                
                # Metadata (store all important fields)
                metadata = {
                    'make': row['Make'],
                    'model': row['Model'],
                    'variant_name': row['Variant'],
                    'price': float(row['price_numeric']),
                    'tier_order': int(row['tier_order']),
                    'tier_name': row['tier_name'],
                    'tier_confidence': row['tier_confidence'],
                    
                    # Store features as JSON strings (ChromaDB doesn't support nested dicts in metadata)
                    'features_safety': str(row['features'].get('safety', []))[:500],  # Truncate to avoid size limits
                    'features_comfort': str(row['features'].get('comfort', []))[:500],
                    'features_technology': str(row['features'].get('technology', []))[:500],
                    'features_exterior': str(row['features'].get('exterior', []))[:500],
                    'features_convenience': str(row['features'].get('convenience', []))[:500],
                    
                    # Add some specs
                    'fuel_type': str(row['Fuel_Type']) if pd.notna(row['Fuel_Type']) else '',
                    'body_type': str(row['Body_Type']) if pd.notna(row['Body_Type']) else '',
                    'seating_capacity': str(row['Seating_Capacity']) if pd.notna(row['Seating_Capacity']) else '',
                }
                
                metadatas.append(metadata)
            
            # Insert batch
            try:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"Batch {batch_num + 1}/{total_batches} inserted ({len(ids)} variants)")
            except Exception as e:
                print(f"Error inserting batch {batch_num + 1}: {e}")
                # Continue with next batch
        
        # Verify count
        count = self.collection.count()
        print(f"\n✅ Ingestion complete! Total variants in DB: {count}")
    
    def get_collection(self):
        """Get the collection object."""
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            return self.collection
        except:
            return None


def main():
    """Main ingestion script."""
    # Paths - use relative paths from project root
    project_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    pickle_path = _os.path.join(project_root, "data/processed/cars_final_processed.pkl")
    db_path = _os.path.join(project_root, "data/car_variants_db")
    
    # Load data
    print("Loading processed data...")
    df = pd.read_pickle(pickle_path)
    print(f"Loaded {len(df)} variants")
    
    # Initialize DB
    db = CarVariantDB(persist_directory=db_path)
    
    # Create collection (reset=True to start fresh)
    db.create_collection(reset=True)
    
    # Ingest data
    db.ingest_data(df, batch_size=100)
    
    # Test query
    print("\n=== Testing Query ===")
    result = db.collection.get(
        where={"$and": [{"make": "Maruti"}, {"model": "Swift"}]},
        limit=5
    )
    
    if result['ids']:
        print(f"Found {len(result['ids'])} Maruti Swift variants:")
        for i, (id, metadata) in enumerate(zip(result['ids'], result['metadatas'])):
            print(f"  {i+1}. {metadata['variant_name']} - ₹{metadata['price']:,.0f} ({metadata['tier_name']})")
    else:
        print("No results found")


if __name__ == "__main__":
    main()
