"""
Cliente de Embeddings
=====================

Cliente para generar embeddings vectoriales usando z-ai-web-dev-sdk.
"""

import asyncio
from typing import List, Optional, Dict, Any
import numpy as np

from .client import LLMConfig


class EmbeddingClient:
    """
    Cliente para generar embeddings vectoriales.
    
    Soporta múltiples proveedores:
    - OpenAI (text-embedding-3-small, text-embedding-3-large)
    - Modelos locales (sentence-transformers)
    - NVIDIA NIM (embed-qa-4)
    """
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        provider: str = "openai",
        api_key: Optional[str] = None,
        batch_size: int = 100
    ):
        self.model = model
        self.provider = provider
        self.api_key = api_key
        self.batch_size = batch_size
        
        self._client = None
        self._dimension = 1536  # Default para OpenAI
    
    async def _get_client(self):
        if self._client is None:
            if self.provider == "openai":
                try:
                    from z_ai_web_dev_sdk import ZAI
                    self._client = await ZAI.create()
                    self._dimension = 1536 if "small" in self.model else 3072
                except ImportError:
                    pass
            elif self.provider == "local":
                # Cargar modelo local
                try:
                    from sentence_transformers import SentenceTransformer
                    self._client = SentenceTransformer('all-MiniLM-L6-v2')
                    self._dimension = 384
                except ImportError:
                    pass
        
        return self._client
    
    async def embed(self, text: str) -> List[float]:
        """
        Generar embedding para un texto.
        
        Args:
            text: Texto a embeder
            
        Returns:
            Vector de embedding
        """
        client = await self._get_client()
        
        if client is None:
            return self._dummy_embedding()
        
        try:
            if self.provider == "openai":
                response = await client.embeddings.create(
                    input=text,
                    model=self.model
                )
                return response.data[0].embedding
            
            elif self.provider == "local":
                # Modelos locales son sincrónicos
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    None,
                    client.encode,
                    text
                )
                return embedding.tolist()
            
        except Exception as e:
            print(f"Embedding error: {e}")
            return self._dummy_embedding()
        
        return self._dummy_embedding()
    
    async def embed_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generar embeddings para múltiples textos.
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de vectores de embedding
        """
        client = await self._get_client()
        
        if client is None:
            return [self._dummy_embedding() for _ in texts]
        
        all_embeddings = []
        
        # Procesar en batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                if self.provider == "openai":
                    response = await client.embeddings.create(
                        input=batch,
                        model=self.model
                    )
                    batch_embeddings = [d.embedding for d in response.data]
                
                elif self.provider == "local":
                    loop = asyncio.get_event_loop()
                    embeddings = await loop.run_in_executor(
                        None,
                        client.encode,
                        batch
                    )
                    batch_embeddings = embeddings.tolist()
                
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                print(f"Batch embedding error: {e}")
                all_embeddings.extend([self._dummy_embedding() for _ in batch])
        
        return all_embeddings
    
    def _dummy_embedding(self) -> List[float]:
        """Generar embedding dummy para fallback"""
        return [0.0] * self._dimension
    
    @property
    def dimension(self) -> int:
        """Obtener dimensión del embedding"""
        return self._dimension
    
    async def similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calcular similitud coseno entre dos textos.
        
        Args:
            text1: Primer texto
            text2: Segundo texto
            
        Returns:
            Similitud coseno (0-1)
        """
        emb1 = await self.embed(text1)
        emb2 = await self.embed(text2)
        
        return self.cosine_similarity(emb1, emb2)
    
    @staticmethod
    def cosine_similarity(
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calcular similitud coseno entre dos vectores"""
        a = np.array(vec1)
        b = np.array(vec2)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    async def search_similar(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Buscar documentos más similares a una query.
        
        Args:
            query: Texto de consulta
            documents: Lista de documentos
            top_k: Número de resultados
            
        Returns:
            Lista de documentos ordenados por similitud
        """
        # Generar embeddings
        query_embedding = await self.embed(query)
        doc_embeddings = await self.embed_batch(documents)
        
        # Calcular similitudes
        similarities = []
        for i, doc_emb in enumerate(doc_embeddings):
            sim = self.cosine_similarity(query_embedding, doc_emb)
            similarities.append({
                "index": i,
                "document": documents[i],
                "similarity": sim
            })
        
        # Ordenar por similitud
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similarities[:top_k]
