#!/usr/bin/env python3
"""
Shakti.py - Neural Network Agent for Exoplanet Analysis
Shakti = Power/Energy in Sanskrit

Handles:
- Machine learning model management (load, save, version control)
- Paper analysis enhancement (SciBERT NER, T5 parameter extraction)
- FITS detection models (Transit detection CNN)
- Training pipeline (offline model training)
- Inference pipeline (real-time predictions)
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np

# PyTorch (already in requirements.txt v2.0)
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available - ML features will be disabled")

# Transformers (already in requirements.txt v2.0)
try:
    from transformers import (
        AutoTokenizer,
        AutoModelForTokenClassification,
        AutoModelForSeq2SeqLM,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available - NLP features will be disabled")


class ShaktiAgent:
    """Neural Network Agent - ML-powered exoplanet analysis"""

    def __init__(self, data_dir: str = "./data", device: str = None):
        """
        Initialize Shakti ML agent

        Args:
            data_dir: Base data directory
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        self.logger = logging.getLogger("Shakti")
        self.data_dir = Path(data_dir)
        self.models_dir = self.data_dir / "models"

        # Create model storage directory
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Detect device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        # Check dependencies
        if not TORCH_AVAILABLE:
            self.logger.error("PyTorch is required. Install with: pip install torch>=2.0.0")

        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers not available. NLP features disabled.")

        # Model registry (in-memory cache)
        self.loaded_models = {}

        # Model configuration
        self.model_config = {
            'paper_analysis': {
                'ner_model': 'allenai/scibert_scivocab_uncased',
                'param_extraction_model': 't5-small'
            },
            'fits_detection': {
                'transit_detector': 'transit_detector_v1.pt'
            }
        }

        self.logger.info(f"Shakti agent initialized (device: {self.device})")

    # ==================== MODEL MANAGEMENT ====================

    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available trained models"""
        models = []

        if not self.models_dir.exists():
            return models

        for model_file in self.models_dir.glob("*.pt"):
            try:
                # Try to load metadata
                metadata_file = model_file.with_suffix('.json')
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                else:
                    metadata = {
                        'name': model_file.stem,
                        'path': str(model_file),
                        'size_mb': model_file.stat().st_size / (1024 * 1024)
                    }

                models.append(metadata)

            except Exception as e:
                self.logger.warning(f"Could not read model {model_file}: {e}")

        return models

    def load_model(self, model_name: str, model_class=None) -> Optional[nn.Module]:
        """
        Load a trained PyTorch model

        Args:
            model_name: Model filename (e.g., 'transit_detector_v1.pt')
            model_class: Model class to instantiate (if None, load state dict only)

        Returns:
            Loaded model or None if failed
        """
        if not TORCH_AVAILABLE:
            self.logger.error("PyTorch not available")
            return None

        # Check cache
        if model_name in self.loaded_models:
            self.logger.info(f"Using cached model: {model_name}")
            return self.loaded_models[model_name]

        model_path = self.models_dir / model_name

        if not model_path.exists():
            self.logger.error(f"Model not found: {model_path}")
            return None

        try:
            # Load model
            if model_class is not None:
                model = model_class()
                model.load_state_dict(torch.load(model_path, map_location=self.device))
                model.to(self.device)
                model.eval()
            else:
                model = torch.load(model_path, map_location=self.device)
                model.eval()

            # Cache
            self.loaded_models[model_name] = model

            self.logger.info(f"Loaded model: {model_name}")
            return model

        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            return None

    def save_model(
        self,
        model: nn.Module,
        model_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a trained model with metadata

        Args:
            model: PyTorch model to save
            model_name: Filename (e.g., 'transit_detector_v1.pt')
            metadata: Optional metadata (metrics, config, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not TORCH_AVAILABLE:
            self.logger.error("PyTorch not available")
            return False

        try:
            model_path = self.models_dir / model_name

            # Save model
            torch.save(model.state_dict(), model_path)

            # Save metadata
            if metadata is not None:
                metadata_path = model_path.with_suffix('.json')
                metadata['saved_at'] = datetime.now().isoformat()
                metadata['model_name'] = model_name
                metadata['path'] = str(model_path)

                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

            self.logger.info(f"Saved model: {model_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")
            return False

    # ==================== PAPER ANALYSIS ENHANCEMENT ====================

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract chemical species and entities using SciBERT NER

        Args:
            text: Input text from research paper

        Returns:
            Dictionary of extracted entities by category

        Note: Phase 1 implementation - uses pretrained SciBERT
        """
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers not available, returning empty results")
            return {'chemical_species': [], 'confidence': 0.0}

        try:
            # Placeholder for Phase 1 implementation
            # Will use: allenai/scibert_scivocab_uncased
            self.logger.info("Entity extraction called (Phase 1 implementation pending)")

            return {
                'chemical_species': [],
                'detection_methods': [],
                'planetary_properties': [],
                'confidence': 0.0,
                'note': 'Phase 1 implementation pending'
            }

        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")
            return {'error': str(e)}

    def extract_parameters(self, text: str) -> Dict[str, Any]:
        """
        Extract numerical parameters using T5 model

        Args:
            text: Input text from research paper

        Returns:
            Structured dictionary with extracted parameters

        Note: Phase 1 implementation - uses fine-tuned T5-small
        """
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers not available, returning empty results")
            return {'parameters': {}, 'confidence': 0.0}

        try:
            # Placeholder for Phase 1 implementation
            # Will use: t5-small fine-tuned on parameter extraction
            self.logger.info("Parameter extraction called (Phase 1 implementation pending)")

            return {
                'parameters': {
                    'mass': None,
                    'radius': None,
                    'period': None,
                    'temperature': None
                },
                'confidence': 0.0,
                'note': 'Phase 1 implementation pending'
            }

        except Exception as e:
            self.logger.error(f"Parameter extraction failed: {e}")
            return {'error': str(e)}

    def classify_paper(self, abstract: str) -> float:
        """
        Classify paper priority/relevance score

        Args:
            abstract: Paper abstract text

        Returns:
            Relevance score (0-1), higher = more relevant

        Note: Phase 1 implementation - uses sentence transformers
        """
        try:
            # Placeholder for Phase 1 implementation
            self.logger.info("Paper classification called (Phase 1 implementation pending)")

            return 0.5  # Neutral score

        except Exception as e:
            self.logger.error(f"Paper classification failed: {e}")
            return 0.0

    # ==================== FITS DETECTION MODELS ====================

    def detect_exoplanet(self, fits_path: str) -> Dict[str, Any]:
        """
        Detect exoplanet in FITS file using trained CNN

        Args:
            fits_path: Path to FITS file

        Returns:
            Detection results with confidence scores

        Note: Phase 3+ implementation - requires trained transit detector
        """
        if not TORCH_AVAILABLE:
            self.logger.error("PyTorch not available")
            return {'error': 'PyTorch not available'}

        try:
            # Placeholder for Phase 3+ implementation
            self.logger.info("Exoplanet detection called (Phase 3 implementation pending)")

            return {
                'has_exoplanet': False,
                'confidence': 0.0,
                'transit_depth': None,
                'period_days': None,
                'model_version': 'none',
                'inference_time_ms': 0.0,
                'note': 'Phase 3 implementation pending - requires trained model'
            }

        except Exception as e:
            self.logger.error(f"Exoplanet detection failed: {e}")
            return {'error': str(e)}

    def batch_inference(self, fits_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Run inference on multiple FITS files

        Args:
            fits_paths: List of FITS file paths

        Returns:
            List of detection results

        Note: Phase 5 implementation - optimized batch processing
        """
        results = []

        for fits_path in fits_paths:
            result = self.detect_exoplanet(fits_path)
            results.append(result)

        return results

    # ==================== TRAINING PIPELINE ====================

    def train_transit_detector(
        self,
        train_data: Optional[Dataset] = None,
        val_data: Optional[Dataset] = None,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 1e-4
    ) -> str:
        """
        Train transit detection CNN model

        Args:
            train_data: Training dataset
            val_data: Validation dataset
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Initial learning rate

        Returns:
            Path to saved model

        Note: Phase 3 implementation - requires synthetic FITS dataset
        """
        if not TORCH_AVAILABLE:
            self.logger.error("PyTorch not available")
            return ""

        try:
            # Placeholder for Phase 3 implementation
            self.logger.info("Training called (Phase 3 implementation pending)")
            self.logger.info(f"Config: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}")

            # Will implement:
            # 1. TransitDetectionCNN model
            # 2. Training loop with AdamW optimizer
            # 3. Validation monitoring
            # 4. Model checkpointing
            # 5. Metrics logging

            return ""

        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            return ""

    def evaluate_model(self, model_name: str) -> Dict[str, float]:
        """
        Evaluate trained model on test set

        Args:
            model_name: Name of model to evaluate

        Returns:
            Dictionary of evaluation metrics

        Note: Phase 3+ implementation
        """
        if not TORCH_AVAILABLE:
            self.logger.error("PyTorch not available")
            return {}

        try:
            # Placeholder for Phase 3+ implementation
            self.logger.info(f"Evaluation called for {model_name} (Phase 3 implementation pending)")

            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'transit_depth_rmse': 0.0,
                'period_rmse': 0.0,
                'note': 'Phase 3 implementation pending'
            }

        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            return {'error': str(e)}

    # ==================== UTILITY METHODS ====================

    def get_device_info(self) -> Dict[str, Any]:
        """Get information about available compute device"""
        info = {
            'device': str(self.device),
            'pytorch_available': TORCH_AVAILABLE,
            'transformers_available': TRANSFORMERS_AVAILABLE
        }

        if TORCH_AVAILABLE and torch.cuda.is_available():
            info['cuda_available'] = True
            info['cuda_device_count'] = torch.cuda.device_count()
            info['cuda_device_name'] = torch.cuda.get_device_name(0)
            info['cuda_memory_gb'] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        else:
            info['cuda_available'] = False

        return info

    def get_status(self) -> Dict[str, Any]:
        """Get agent status and configuration"""
        return {
            'agent': 'Shakti',
            'version': '1.0.0',
            'device': str(self.device),
            'models_dir': str(self.models_dir),
            'available_models': len(self.list_available_models()),
            'loaded_models': len(self.loaded_models),
            'capabilities': {
                'paper_analysis': TRANSFORMERS_AVAILABLE,
                'fits_detection': TORCH_AVAILABLE,
                'training': TORCH_AVAILABLE
            }
        }


# ==================== NEURAL NETWORK ARCHITECTURES ====================

class TransitDetectionCNN(nn.Module):
    """
    Convolutional Neural Network for exoplanet transit detection

    Input: 1D light curve (flux vs time, 1000 points)
    Output: [has_transit (binary), transit_depth (float), period (float)]

    Note: Phase 3 implementation - currently a skeleton
    """

    def __init__(self, input_size: int = 1000):
        super(TransitDetectionCNN, self).__init__()

        self.input_size = input_size

        # Convolutional feature extraction
        self.conv_layers = nn.Sequential(
            # Conv block 1: 1 -> 32 channels
            nn.Conv1d(1, 32, kernel_size=9, padding=4),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),

            # Conv block 2: 32 -> 64 channels
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),

            # Conv block 3: 64 -> 128 channels
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2)
        )

        # Calculate flattened size after convolutions
        # input_size=1000 -> after 3 MaxPool(2): 1000/2/2/2 = 125
        self.flattened_size = 128 * (input_size // 8)

        # Dense layers
        self.fc_layers = nn.Sequential(
            nn.Linear(self.flattened_size, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),

            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3)
        )

        # Multi-head output
        self.classification_head = nn.Linear(128, 1)  # Binary: has transit?
        self.depth_head = nn.Linear(128, 1)           # Regression: transit depth
        self.period_head = nn.Linear(128, 1)          # Regression: period

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input tensor [batch_size, 1, 1000]

        Returns:
            Tuple of (classification_logits, transit_depth, period)
        """
        # Convolutional feature extraction
        features = self.conv_layers(x)

        # Flatten
        features = features.view(features.size(0), -1)

        # Dense layers
        features = self.fc_layers(features)

        # Multi-head predictions
        has_transit = self.classification_head(features)
        transit_depth = self.depth_head(features)
        period = self.period_head(features)

        return has_transit, transit_depth, period


# ==================== MAIN / TESTING ====================

if __name__ == "__main__":
    # Basic testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Shakti Agent - Neural Network Module")
    print("=" * 60)

    # Initialize agent
    agent = ShaktiAgent()

    # Display status
    status = agent.get_status()
    print("\nAgent Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    # Display device info
    device_info = agent.get_device_info()
    print("\nDevice Information:")
    for key, value in device_info.items():
        print(f"  {key}: {value}")

    # List available models
    models = agent.list_available_models()
    print(f"\nAvailable Models: {len(models)}")
    for model in models:
        print(f"  - {model.get('name', 'Unknown')}")

    # Test TransitDetectionCNN architecture
    if TORCH_AVAILABLE:
        print("\nTesting TransitDetectionCNN architecture...")
        model = TransitDetectionCNN(input_size=1000)
        print(f"  Model parameters: {sum(p.numel() for p in model.parameters()):,}")

        # Test forward pass with dummy data
        dummy_input = torch.randn(4, 1, 1000)  # batch_size=4
        has_transit, depth, period = model(dummy_input)
        print(f"  Output shapes: has_transit={has_transit.shape}, depth={depth.shape}, period={period.shape}")

    print("\n" + "=" * 60)
    print("Shakti Agent initialized successfully!")
    print("Ready for Phase 1+ implementation.")
    print("=" * 60)
