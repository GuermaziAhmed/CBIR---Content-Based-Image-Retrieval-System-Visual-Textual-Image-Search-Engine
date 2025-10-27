"""
VGG Feature Extractor for Image Search
Supports VGG16 and VGG19 models with TensorFlow/Keras
"""

import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications import VGG16, VGG19
from tensorflow.keras.applications.vgg16 import preprocess_input as vgg16_preprocess
from tensorflow.keras.applications.vgg19 import preprocess_input as vgg19_preprocess
from tensorflow.keras.preprocessing import image as keras_image
from typing import Union, Tuple
import os


class VGGFeatureExtractor:
    """
    Extract deep features from images using VGG16 or VGG19
    """
    
    def __init__(
        self,
        model_name: str = "vgg16",
        layer_name: str = "fc2",
        weights: str = "imagenet",
        input_size: Tuple[int, int] = (224, 224)
    ):
        """
        Initialize VGG feature extractor
        
        Args:
            model_name: "vgg16" or "vgg19"
            layer_name: Layer to extract features from
                       - "fc2": 4096-dim dense layer (default)
                       - "fc1": 4096-dim dense layer
                       - "block5_pool": 512-dim pooled features
                       - "flatten": 25088-dim flattened features
            weights: "imagenet" for pre-trained weights
            input_size: Image size (width, height)
        """
        self.model_name = model_name.lower()
        self.layer_name = layer_name
        self.input_size = input_size
        
        print(f"🔧 Initializing {model_name.upper()} feature extractor...")
        print(f"   Layer: {layer_name}")
        print(f"   Input size: {input_size}")
        
        # Load pre-trained model
        if self.model_name == "vgg16":
            base_model = VGG16(weights=weights, include_top=True)
            self.preprocess = vgg16_preprocess
        elif self.model_name == "vgg19":
            base_model = VGG19(weights=weights, include_top=True)
            self.preprocess = vgg19_preprocess
        else:
            raise ValueError(f"Unsupported model: {model_name}. Use 'vgg16' or 'vgg19'")
        
        # Create feature extraction model
        try:
            layer = base_model.get_layer(layer_name)
            self.model = tf.keras.Model(
                inputs=base_model.input,
                outputs=layer.output
            )
            self.feature_dim = layer.output_shape[-1]
            print(f"✅ Model loaded. Feature dimension: {self.feature_dim}")
        except Exception as e:
            raise ValueError(f"Layer '{layer_name}' not found. Error: {e}")
    
    def load_image(self, image_path: str) -> np.ndarray:
        """
        Load and preprocess image
        """
        try:
            img = keras_image.load_img(
                image_path,
                target_size=self.input_size
            )
            img_array = keras_image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = self.preprocess(img_array)
            return img_array
        except Exception as e:
            raise IOError(f"Error loading image {image_path}: {e}")
    
    def load_image_from_array(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess image from NumPy array
        """
        try:
            # Resize if needed
            if img.shape[:2] != self.input_size:
                pil_img = Image.fromarray(img.astype('uint8'))
                pil_img = pil_img.resize(self.input_size, Image.LANCZOS)
                img = np.array(pil_img)
            
            img_array = np.expand_dims(img, axis=0)
            img_array = self.preprocess(img_array)
            return img_array
        except Exception as e:
            raise ValueError(f"Error preprocessing image array: {e}")
    
    def extract_features(self, image_input: Union[str, np.ndarray]) -> np.ndarray:
        """
        Extract features from image
        
        Args:
            image_input: Path to image file or NumPy array
            
        Returns:
            Feature vector (1D numpy array)
        """
        try:
            # Load and preprocess
            if isinstance(image_input, str):
                img_array = self.load_image(image_input)
            else:
                img_array = self.load_image_from_array(image_input)
            
            # Extract features
            features = self.model.predict(img_array, verbose=0)
            
            # Flatten if needed
            features = features.flatten()
            
            # L2 normalize
            features = features / (np.linalg.norm(features) + 1e-8)
            
            return features
        
        except Exception as e:
            raise RuntimeError(f"Feature extraction failed: {e}")
    
    def extract_batch(self, image_paths: list) -> np.ndarray:
        """
        Extract features from multiple images (batch processing)
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            2D numpy array (num_images, feature_dim)
        """
        batch_features = []
        
        for i, img_path in enumerate(image_paths):
            try:
                features = self.extract_features(img_path)
                batch_features.append(features)
                
                if (i + 1) % 100 == 0:
                    print(f"  Processed {i + 1}/{len(image_paths)} images")
            
            except Exception as e:
                print(f"⚠️ Error processing {img_path}: {e}")
                # Add zero vector for failed images
                batch_features.append(np.zeros(self.feature_dim))
        
        return np.array(batch_features)
    
    def get_model_info(self) -> dict:
        """
        Get model information
        """
        return {
            "model_name": self.model_name,
            "layer_name": self.layer_name,
            "feature_dim": self.feature_dim,
            "input_size": self.input_size
        }


# Utility functions

def compare_images(
    extractor: VGGFeatureExtractor,
    image1: Union[str, np.ndarray],
    image2: Union[str, np.ndarray],
    metric: str = "cosine"
) -> float:
    """
    Compare similarity between two images
    
    Args:
        extractor: VGG feature extractor
        image1, image2: Image paths or arrays
        metric: "cosine" or "euclidean"
        
    Returns:
        Similarity score (higher = more similar for cosine)
    """
    feat1 = extractor.extract_features(image1)
    feat2 = extractor.extract_features(image2)
    
    if metric == "cosine":
        # Cosine similarity
        return np.dot(feat1, feat2)
    elif metric == "euclidean":
        # Euclidean distance (lower = more similar)
        return -np.linalg.norm(feat1 - feat2)
    else:
        raise ValueError(f"Unknown metric: {metric}")


# Example usage
if __name__ == "__main__":
    import sys
    
    # Initialize extractor
    print("\n" + "="*60)
    print("VGG Feature Extractor Test")
    print("="*60 + "\n")
    
    # Test VGG16
    extractor_vgg16 = VGGFeatureExtractor(
        model_name="vgg16",
        layer_name="fc2"  # 4096-dim
    )
    
    # Test VGG16 with pooling layer (smaller features)
    extractor_vgg16_pool = VGGFeatureExtractor(
        model_name="vgg16",
        layer_name="block5_pool"  # 512-dim after global pooling
    )
    
    print("\n" + "="*60)
    print("Model Information:")
    print("="*60)
    print(f"VGG16 FC2: {extractor_vgg16.get_model_info()}")
    print(f"VGG16 Pool5: {extractor_vgg16_pool.get_model_info()}")
    
    # Test with an image if provided
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        if os.path.exists(test_image):
            print(f"\n📸 Testing with image: {test_image}")
            
            # Extract features
            features_fc2 = extractor_vgg16.extract_features(test_image)
            features_pool = extractor_vgg16_pool.extract_features(test_image)
            
            print(f"\n✅ Feature extraction successful!")
            print(f"   FC2 features: shape={features_fc2.shape}, norm={np.linalg.norm(features_fc2):.4f}")
            print(f"   Pool5 features: shape={features_pool.shape}, norm={np.linalg.norm(features_pool):.4f}")
            print(f"\n   Sample FC2 values: {features_fc2[:10]}")
        else:
            print(f"❌ Image not found: {test_image}")
    else:
        print("\n💡 Usage: python vgg_extractor.py <image_path>")
    
    print("\n" + "="*60)
    print("✅ Test complete!")
    print("="*60 + "\n")
