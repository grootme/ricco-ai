"""
RICCO AI Service - TensorFlow/Keras ML Service
Servicio de Machine Learning con TensorFlow y Keras para RICCO
"""

import asyncio
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field
from structlog import get_logger

from app.core.config import settings

logger = get_logger(__name__)


# ============================================
# ML Models
# ============================================

class ModelType(str):
    """ML model types"""
    IMAGE_CLASSIFIER = "image_classifier"
    OBJECT_DETECTOR = "object_detector"
    TEXT_CLASSIFIER = "text_classifier"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    RECOMMENDER = "recommender"
    ANOMALY_DETECTOR = "anomaly_detector"
    FORECAST = "forecast"
    EMBEDDING = "embedding"


class ModelConfig(BaseModel):
    """Model configuration"""
    name: str
    type: str
    version: str = "1.0.0"
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None
    labels: Optional[List[str]] = None
    preprocessing: Optional[Dict[str, Any]] = None
    postprocessing: Optional[Dict[str, Any]] = None


class PredictionRequest(BaseModel):
    """Prediction request"""
    model_name: str
    input_data: Union[List[float], List[List[float]], str]
    return_probabilities: bool = False
    return_features: bool = False


class PredictionResult(BaseModel):
    """Prediction result"""
    prediction_id: str
    model_name: str
    predictions: List[Any]
    probabilities: Optional[List[float]] = None
    features: Optional[List[float]] = None
    confidence: float
    latency_ms: float


class TrainingRequest(BaseModel):
    """Training request"""
    model_name: str
    dataset_path: str
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
    validation_split: float = 0.2
    callbacks: Optional[Dict[str, Any]] = None


class TrainingResult(BaseModel):
    """Training result"""
    training_id: str
    model_name: str
    epochs_completed: int
    final_loss: float
    final_accuracy: Optional[float] = None
    training_time_seconds: float
    model_path: str


# ============================================
# TensorFlow Service
# ============================================

class TensorFlowService:
    """
    Servicio de TensorFlow/Keras para ML tradicional
    Soporta clasificación de imágenes, texto, detección de anomalías, etc.
    """
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._model_configs: Dict[str, ModelConfig] = {}
        self._initialized = False
        
    async def initialize(self):
        """Initialize TensorFlow and load default models"""
        if self._initialized:
            return
            
        try:
            # Lazy import TensorFlow
            import tensorflow as tf
            
            # Configure TensorFlow
            tf.config.optimizer.set_jit(True)  # Enable XLA
            
            logger.info(f"TensorFlow version: {tf.__version__}")
            
            # Load pre-built models
            await self._load_default_models()
            
            self._initialized = True
            logger.info("TensorFlow service initialized")
            
        except ImportError:
            logger.warning("TensorFlow not installed, using fallback mode")
            self._initialized = True
    
    async def _load_default_models(self):
        """Load default pre-trained models"""
        try:
            # Image classification model
            await self._load_image_classifier()
            
            # Text classification model
            await self._load_text_classifier()
            
            # Anomaly detection model
            await self._load_anomaly_detector()
            
        except Exception as e:
            logger.error(f"Error loading default models: {e}")
    
    async def _load_image_classifier(self):
        """Load MobileNetV2 for image classification"""
        try:
            import tensorflow as tf
            from tensorflow.keras.applications import MobileNetV2
            from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
            
            model = MobileNetV2(weights='imagenet')
            
            self._models['imagenet_classifier'] = model
            self._model_configs['imagenet_classifier'] = ModelConfig(
                name='imagenet_classifier',
                type=ModelType.IMAGE_CLASSIFIER,
                input_shape=[224, 224, 3],
                labels=['imagenet_1000_classes'],
                preprocessing={'normalize': True, 'size': [224, 224]},
            )
            
            logger.info("MobileNetV2 image classifier loaded")
            
        except Exception as e:
            logger.warning(f"Could not load image classifier: {e}")
    
    async def _load_text_classifier(self):
        """Load text classification model"""
        # In production, load a pre-trained text model
        # For now, create a simple model
        try:
            import tensorflow as tf
            from tensorflow.keras import layers, models
            
            # Simple text classifier
            model = models.Sequential([
                layers.Embedding(10000, 128, input_length=100),
                layers.GlobalAveragePooling1D(),
                layers.Dense(64, activation='relu'),
                layers.Dropout(0.5),
                layers.Dense(3, activation='softmax')  # positive, negative, neutral
            ])
            
            model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            self._models['sentiment_analyzer'] = model
            self._model_configs['sentiment_analyzer'] = ModelConfig(
                name='sentiment_analyzer',
                type=ModelType.SENTIMENT_ANALYZER,
                input_shape=[100],
                labels=['negative', 'neutral', 'positive'],
            )
            
            logger.info("Sentiment analyzer model loaded")
            
        except Exception as e:
            logger.warning(f"Could not load text classifier: {e}")
    
    async def _load_anomaly_detector(self):
        """Load anomaly detection model"""
        try:
            import tensorflow as tf
            from tensorflow.keras import layers, models
            
            # Autoencoder for anomaly detection
            input_dim = 100
            
            encoder = models.Sequential([
                layers.Input(shape=(input_dim,)),
                layers.Dense(64, activation='relu'),
                layers.Dense(32, activation='relu'),
                layers.Dense(16, activation='relu'),
            ])
            
            decoder = models.Sequential([
                layers.Input(shape=(16,)),
                layers.Dense(32, activation='relu'),
                layers.Dense(64, activation='relu'),
                layers.Dense(input_dim, activation='sigmoid'),
            ])
            
            autoencoder = models.Sequential([encoder, decoder])
            autoencoder.compile(optimizer='adam', loss='mse')
            
            self._models['anomaly_detector'] = autoencoder
            self._model_configs['anomaly_detector'] = ModelConfig(
                name='anomaly_detector',
                type=ModelType.ANOMALY_DETECTOR,
                input_shape=[input_dim],
            )
            
            logger.info("Anomaly detector model loaded")
            
        except Exception as e:
            logger.warning(f"Could not load anomaly detector: {e}")
    
    # ============================================
    # Prediction Methods
    # ============================================
    
    async def predict(self, request: PredictionRequest) -> PredictionResult:
        """
        Make a prediction using a loaded model
        
        Args:
            request: Prediction request
            
        Returns:
            Prediction result
        """
        start_time = time.time()
        
        await self.initialize()
        
        model_name = request.model_name
        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' not found")
        
        model = self._models[model_name]
        config = self._model_configs[model_name]
        
        # Prepare input
        input_data = await self._preprocess_input(request.input_data, config)
        
        # Run prediction
        loop = asyncio.get_event_loop()
        predictions = await loop.run_in_executor(
            None,
            model.predict,
            input_data
        )
        
        # Post-process
        result = await self._postprocess_output(
            predictions, 
            config,
            return_probabilities=request.return_probabilities,
            return_features=request.return_features
        )
        
        return PredictionResult(
            prediction_id=str(uuid.uuid4()),
            model_name=model_name,
            predictions=result['predictions'],
            probabilities=result.get('probabilities'),
            features=result.get('features'),
            confidence=result.get('confidence', 0.0),
            latency_ms=(time.time() - start_time) * 1000,
        )
    
    async def _preprocess_input(
        self,
        input_data: Union[List[float], str, bytes],
        config: ModelConfig,
    ) -> np.ndarray:
        """Preprocess input data for model"""
        import tensorflow as tf
        
        if config.type == ModelType.IMAGE_CLASSIFIER:
            # Image preprocessing
            if isinstance(input_data, str):
                # Assume base64 or URL
                import base64
                from PIL import Image
                
                try:
                    image_data = base64.b64decode(input_data)
                    image = Image.open(BytesIO(image_data))
                except:
                    # Try as file path
                    image = Image.open(input_data)
                
                # Resize to expected size
                image = image.resize((224, 224))
                image_array = np.array(image)
                
                if image_array.shape[-1] == 4:  # RGBA
                    image_array = image_array[..., :3]
                
                # Apply MobileNet preprocessing
                from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
                image_array = preprocess_input(image_array)
                
                return np.expand_dims(image_array, axis=0)
            
            elif isinstance(input_data, bytes):
                from PIL import Image
                image = Image.open(BytesIO(input_data))
                image = image.resize((224, 224))
                image_array = np.array(image)
                if image_array.shape[-1] == 4:
                    image_array = image_array[..., :3]
                return np.expand_dims(image_array, axis=0)
        
        elif config.type in [ModelType.TEXT_CLASSIFIER, ModelType.SENTIMENT_ANALYZER]:
            # Text preprocessing
            if isinstance(input_data, str):
                # Tokenize text
                from tensorflow.keras.preprocessing.text import Tokenizer
                from tensorflow.keras.preprocessing.sequence import pad_sequences
                
                tokenizer = Tokenizer(num_words=10000)
                tokenizer.fit_on_texts([input_data])
                sequences = tokenizer.texts_to_sequences([input_data])
                return pad_sequences(sequences, maxlen=100)
        
        elif config.type == ModelType.ANOMALY_DETECTOR:
            # Numeric input
            if isinstance(input_data, list):
                return np.array([input_data])
        
        # Default: convert to numpy array
        return np.array([input_data])
    
    async def _postprocess_output(
        self,
        predictions: np.ndarray,
        config: ModelConfig,
        return_probabilities: bool = False,
        return_features: bool = False,
    ) -> Dict[str, Any]:
        """Post-process model output"""
        result = {
            'predictions': [],
            'confidence': 0.0,
        }
        
        if config.type == ModelType.IMAGE_CLASSIFIER:
            from tensorflow.keras.applications.mobilenet_v2 import decode_predictions
            
            decoded = decode_predictions(predictions, top=5)[0]
            result['predictions'] = [
                {'label': label, 'description': desc, 'score': float(score)}
                for (_, label, desc, score) in decoded
            ]
            result['confidence'] = float(decoded[0][2]) if decoded else 0.0
            
            if return_probabilities:
                result['probabilities'] = predictions.flatten().tolist()
        
        elif config.type in [ModelType.TEXT_CLASSIFIER, ModelType.SENTIMENT_ANALYZER]:
            pred = predictions[0]
            labels = config.labels or ['negative', 'neutral', 'positive']
            predicted_class = np.argmax(pred)
            
            result['predictions'] = [{
                'label': labels[predicted_class],
                'score': float(pred[predicted_class]),
            }]
            result['confidence'] = float(pred[predicted_class])
            
            if return_probabilities:
                result['probabilities'] = pred.tolist()
        
        elif config.type == ModelType.ANOMALY_DETECTOR:
            # Reconstruction error as anomaly score
            reconstruction_error = float(np.mean(np.square(predictions)))
            is_anomaly = reconstruction_error > 0.1  # Threshold
            
            result['predictions'] = [{
                'is_anomaly': is_anomaly,
                'reconstruction_error': reconstruction_error,
                'threshold': 0.1,
            }]
            result['confidence'] = min(reconstruction_error / 0.1, 1.0)
        
        return result
    
    # ============================================
    # Model Management
    # ============================================
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all loaded models"""
        return [
            {
                'name': name,
                'type': config.type,
                'version': config.version,
                'input_shape': config.input_shape,
                'labels_count': len(config.labels) if config.labels else 0,
            }
            for name, config in self._model_configs.items()
        ]
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get model information"""
        if model_name not in self._model_configs:
            raise ValueError(f"Model '{model_name}' not found")
        
        config = self._model_configs[model_name]
        return config.model_dump()
    
    async def load_custom_model(
        self,
        model_path: str,
        config: ModelConfig,
    ) -> Dict[str, Any]:
        """Load a custom model from path"""
        import tensorflow as tf
        
        model = tf.keras.models.load_model(model_path)
        
        self._models[config.name] = model
        self._model_configs[config.name] = config
        
        return {
            'name': config.name,
            'loaded': True,
            'input_shape': model.input_shape,
            'output_shape': model.output_shape,
        }
    
    # ============================================
    # RICCO-Specific ML Functions
    # ============================================
    
    async def classify_product_image(
        self,
        image_data: Union[str, bytes],
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Classify a product image
        
        Args:
            image_data: Image data (base64, bytes, or path)
            categories: Optional custom categories
            
        Returns:
            Classification result
        """
        request = PredictionRequest(
            model_name='imagenet_classifier',
            input_data=image_data,
            return_probabilities=True,
        )
        
        result = await self.predict(request)
        
        return {
            'top_prediction': result.predictions[0] if result.predictions else None,
            'all_predictions': result.predictions,
            'confidence': result.confidence,
            'latency_ms': result.latency_ms,
        }
    
    async def analyze_document_image(
        self,
        image_data: Union[str, bytes],
    ) -> Dict[str, Any]:
        """
        Analyze a document image (ID, passport, etc.)
        
        Args:
            image_data: Document image
            
        Returns:
            Analysis result
        """
        # First classify what type of document
        request = PredictionRequest(
            model_name='imagenet_classifier',
            input_data=image_data,
        )
        
        result = await self.predict(request)
        
        # Check if it looks like a document
        document_keywords = ['envelope', 'letter', 'notebook', 'binder', 'book']
        is_document = any(
            any(kw in pred.get('description', '').lower() for kw in document_keywords)
            for pred in result.predictions
        )
        
        return {
            'is_document': is_document,
            'document_type': result.predictions[0] if result.predictions else None,
            'confidence': result.confidence,
        }
    
    async def detect_anomalies(
        self,
        data: List[float],
        threshold: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Detect anomalies in data
        
        Args:
            data: Input data
            threshold: Anomaly threshold
            
        Returns:
            Anomaly detection result
        """
        request = PredictionRequest(
            model_name='anomaly_detector',
            input_data=data,
        )
        
        result = await self.predict(request)
        
        return {
            'is_anomaly': result.predictions[0].get('is_anomaly', False),
            'anomaly_score': result.predictions[0].get('reconstruction_error', 0),
            'threshold': threshold,
            'confidence': result.confidence,
        }
    
    async def analyze_sentiment(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Input text
            
        Returns:
            Sentiment analysis result
        """
        request = PredictionRequest(
            model_name='sentiment_analyzer',
            input_data=text,
            return_probabilities=True,
        )
        
        result = await self.predict(request)
        
        return {
            'sentiment': result.predictions[0].get('label', 'neutral'),
            'confidence': result.confidence,
            'probabilities': result.probabilities,
        }
    
    # ============================================
    # Health Check
    # ============================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check TensorFlow service health"""
        try:
            await self.initialize()
            
            return {
                'initialized': self._initialized,
                'models_loaded': len(self._models),
                'models': list(self._models.keys()),
            }
        except Exception as e:
            return {
                'initialized': False,
                'error': str(e),
            }


# Singleton
_tensorflow_service: Optional[TensorFlowService] = None

def get_tensorflow_service() -> TensorFlowService:
    global _tensorflow_service
    if _tensorflow_service is None:
        _tensorflow_service = TensorFlowService()
    return _tensorflow_service
