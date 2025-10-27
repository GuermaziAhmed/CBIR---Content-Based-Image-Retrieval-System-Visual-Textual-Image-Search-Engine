"""
Descriptor Extractor Module
Implements various image descriptors: Color Histogram, LBP, HOG, MPEG-7
"""

import cv2
import numpy as np
from skimage.feature import local_binary_pattern, hog
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DescriptorExtractor:
    """Base class for all descriptor extractors"""
    
    @staticmethod
    def normalize_vector(vector: np.ndarray) -> np.ndarray:
        """L2 normalization"""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm


class ColorHistogramExtractor(DescriptorExtractor):
    """Extract RGB color histogram"""
    
    def __init__(self, bins: int = 8):
        self.bins = bins
        self.dimension = bins * 3  # RGB channels
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        Extract color histogram from image
        
        Args:
            image: RGB image as numpy array (H, W, 3)
            
        Returns:
            Normalized histogram vector of size (bins*3,)
        """
        try:
            # Ensure RGB format
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            
            # Calculate histogram for each channel
            histograms = []
            for i in range(3):  # R, G, B
                hist = cv2.calcHist([image], [i], None, [self.bins], [0, 256])
                histograms.append(hist.flatten())
            
            # Concatenate and normalize
            descriptor = np.concatenate(histograms)
            descriptor = self.normalize_vector(descriptor)
            
            return descriptor.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Color histogram extraction failed: {e}")
            return np.zeros(self.dimension, dtype=np.float32)


class LBPExtractor(DescriptorExtractor):
    """Extract Local Binary Pattern features"""
    
    def __init__(self, n_points: int = 8, radius: int = 1, method: str = 'uniform'):
        self.n_points = n_points
        self.radius = radius
        self.method = method
        # For uniform LBP, dimension is n_points + 2
        self.dimension = n_points + 2 if method == 'uniform' else 2 ** n_points
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        Extract LBP histogram from image
        
        Args:
            image: RGB or grayscale image
            
        Returns:
            LBP histogram vector
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Compute LBP
            lbp = local_binary_pattern(
                gray,
                P=self.n_points,
                R=self.radius,
                method=self.method
            )
            
            # Calculate histogram
            n_bins = int(lbp.max() + 1)
            hist, _ = np.histogram(
                lbp.ravel(),
                bins=n_bins,
                range=(0, n_bins),
                density=True
            )
            
            # Normalize
            descriptor = self.normalize_vector(hist)
            
            return descriptor.astype(np.float32)
            
        except Exception as e:
            logger.error(f"LBP extraction failed: {e}")
            return np.zeros(self.dimension, dtype=np.float32)


class HOGExtractor(DescriptorExtractor):
    """Extract Histogram of Oriented Gradients"""
    
    def __init__(
        self,
        orientations: int = 9,
        pixels_per_cell: tuple = (8, 8),
        cells_per_block: tuple = (3, 3)
    ):
        self.orientations = orientations
        self.pixels_per_cell = pixels_per_cell
        self.cells_per_block = cells_per_block
        # Dimension depends on image size, will be set dynamically
        self.dimension = None
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        Extract HOG features from image
        
        Args:
            image: RGB or grayscale image
            
        Returns:
            HOG feature vector
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Resize to standard size for consistent descriptor length
            standard_size = (128, 128)
            resized = cv2.resize(gray, standard_size)
            
            # Extract HOG features
            features = hog(
                resized,
                orientations=self.orientations,
                pixels_per_cell=self.pixels_per_cell,
                cells_per_block=self.cells_per_block,
                block_norm='L2-Hys',
                visualize=False,
                feature_vector=True
            )
            
            # Normalize
            descriptor = self.normalize_vector(features)
            
            if self.dimension is None:
                self.dimension = len(descriptor)
            
            return descriptor.astype(np.float32)
            
        except Exception as e:
            logger.error(f"HOG extraction failed: {e}")
            # Return zero vector with standard dimension
            return np.zeros(81, dtype=np.float32)


class MPEG7Extractor(DescriptorExtractor):
    """
    MPEG-7 descriptor extractor
    Simplified implementation - in production, use pre-computed XML descriptors
    """
    
    def __init__(self):
        self.dimension = 64  # Placeholder dimension
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        Extract MPEG-7 compatible features
        This is a simplified version using color and edge information
        
        Args:
            image: RGB image
            
        Returns:
            MPEG-7 style feature vector
        """
        try:
            # Simplified MPEG-7: combine color moments and edge histogram
            
            # Color moments (mean, std for each channel)
            color_moments = []
            for i in range(3):
                channel = image[:, :, i] if len(image.shape) == 3 else image
                color_moments.extend([
                    np.mean(channel),
                    np.std(channel)
                ])
            
            # Edge histogram (using Sobel)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            # Edge magnitude histogram
            magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
            edge_hist, _ = np.histogram(magnitude.ravel(), bins=32, range=(0, 256))
            
            # Combine features
            descriptor = np.concatenate([
                color_moments,
                edge_hist / (edge_hist.sum() + 1e-7)
            ])
            
            # Pad or truncate to fixed dimension
            if len(descriptor) < self.dimension:
                descriptor = np.pad(descriptor, (0, self.dimension - len(descriptor)))
            else:
                descriptor = descriptor[:self.dimension]
            
            descriptor = self.normalize_vector(descriptor)
            
            return descriptor.astype(np.float32)
            
        except Exception as e:
            logger.error(f"MPEG-7 extraction failed: {e}")
            return np.zeros(self.dimension, dtype=np.float32)


# Factory function
def extract_all_descriptors(
    image: np.ndarray,
    descriptor_names: list
) -> Dict[str, Optional[np.ndarray]]:
    """
    Extract multiple descriptors from an image
    
    Args:
        image: Input image as numpy array
        descriptor_names: List of descriptor names to extract
        
    Returns:
        Dictionary mapping descriptor name to feature vector
    """
    extractors = {
        'color': ColorHistogramExtractor(bins=8),
        'lbp': LBPExtractor(n_points=8, radius=1),
        'hog': HOGExtractor(),
        'mpeg7': MPEG7Extractor()
    }
    
    results = {}
    for name in descriptor_names:
        if name in extractors:
            try:
                results[name] = extractors[name].extract(image)
            except Exception as e:
                logger.error(f"Failed to extract {name}: {e}")
                results[name] = None
        else:
            logger.warning(f"Unknown descriptor: {name}")
            results[name] = None
    
    return results


# Utility function for batch extraction
def extract_descriptors_batch(
    images: list,
    descriptor_names: list
) -> list:
    """
    Extract descriptors from multiple images
    
    Args:
        images: List of images as numpy arrays
        descriptor_names: List of descriptor names
        
    Returns:
        List of descriptor dictionaries
    """
    return [extract_all_descriptors(img, descriptor_names) for img in images]
