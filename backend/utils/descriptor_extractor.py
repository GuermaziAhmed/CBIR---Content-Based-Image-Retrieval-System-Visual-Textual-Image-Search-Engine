"""
Descriptor Extractor Module
Implements various image descriptors: Color Histogram, LBP, HOG
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
            
            # Concatenate histograms
            descriptor = np.concatenate(histograms)
            
            # L1 normalization (sum to 1) - required for proper histogram comparison
            # This ensures Chi-Square and Bhattacharyya distances work correctly
            sum_hist = np.sum(descriptor)
            if sum_hist > 0:
                descriptor = descriptor / sum_hist
            
            # Add small epsilon to avoid division by zero in distance calculations
            descriptor = descriptor + 1e-10
            
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
            HOG feature vector (81-dim)
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # CRITICAL: Resize to standard size BEFORE HOG extraction
            # This ensures consistent 81-dim output regardless of input size
            standard_size = (128, 128)
            resized = cv2.resize(gray, standard_size, interpolation=cv2.INTER_AREA)
            
            # Extract HOG features with fixed parameters
            features = hog(
                resized,
                orientations=self.orientations,
                pixels_per_cell=self.pixels_per_cell,
                cells_per_block=self.cells_per_block,
                block_norm='L2-Hys',
                visualize=False,
                feature_vector=True
            )
            
            # Ensure consistent dimension
            # With 128x128 image, 8x8 cells, 3x3 blocks, 9 orientations = 81 dims
            if len(features) != 81:
                logger.warning(f"HOG produced {len(features)} dims instead of 81, padding/truncating")
                if len(features) < 81:
                    features = np.pad(features, (0, 81 - len(features)))
                else:
                    features = features[:81]
            
            # Normalize
            descriptor = self.normalize_vector(features)
            
            if self.dimension is None:
                self.dimension = 81
            
            return descriptor.astype(np.float32)
            
        except Exception as e:
            logger.error(f"HOG extraction failed: {e}")
            # Return zero vector with standard dimension
            return np.zeros(81, dtype=np.float32)


class EdgeHistogramExtractor(DescriptorExtractor):
    """
    Edge Histogram Descriptor
    Captures edge distribution in different orientations
    """
    
    def __init__(self, bins: int = 64):
        self.bins = bins
        self.dimension = bins
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        Extract edge histogram using Sobel gradients
        
        Args:
            image: RGB or grayscale image
            
        Returns:
            Edge histogram feature vector
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Compute gradients using Sobel
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            # Compute magnitude and orientation
            magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
            orientation = np.arctan2(sobel_y, sobel_x)
            
            # Create histogram of edge orientations weighted by magnitude
            # Orientations range from -π to π
            hist, _ = np.histogram(
                orientation.ravel(),
                bins=self.bins,
                range=(-np.pi, np.pi),
                weights=magnitude.ravel()
            )
            
            # L2 normalization for cosine similarity
            norm = np.linalg.norm(hist)
            if norm > 1e-7:
                descriptor = hist / norm
            else:
                descriptor = hist
            
            return descriptor.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Edge histogram extraction failed: {e}")
            return np.zeros(self.dimension, dtype=np.float32)


class SIFTExtractor(DescriptorExtractor):
    """
    SIFT (Scale-Invariant Feature Transform) Descriptor
    Uses RootSIFT normalization and statistical pooling for better discriminability
    """
    
    def __init__(self, n_features: int = 100, descriptor_size: int = 128):
        """
        Args:
            n_features: Maximum number of SIFT keypoints to detect
            descriptor_size: Size of aggregated descriptor (128 for standard SIFT)
        """
        self.n_features = n_features
        self.descriptor_size = descriptor_size
        # Use half dimension for mean, half for std (64 + 64 = 128)
        self.dimension = descriptor_size
        
        # Initialize SIFT detector
        try:
            self.sift = cv2.SIFT_create(nfeatures=n_features)
        except AttributeError:
            # Fallback for older OpenCV versions
            self.sift = cv2.xfeatures2d.SIFT_create(nfeatures=n_features)
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        Extract SIFT features using RootSIFT + mean/std pooling aggregation
        
        This uses both mean and standard deviation pooling which captures
        more information than max pooling alone. The combination of mean
        and std creates a more robust global descriptor.
        
        Args:
            image: RGB or grayscale image
            
        Returns:
            Aggregated SIFT descriptor vector
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Detect keypoints and compute descriptors
            keypoints, descriptors = self.sift.detectAndCompute(gray, None)
            
            if descriptors is None or len(descriptors) == 0:
                logger.warning("No SIFT keypoints detected")
                return np.zeros(self.dimension, dtype=np.float32)
            
            # Apply RootSIFT normalization (Arandjelovic & Zisserman, 2012)
            # This significantly improves discriminability
            eps = 1e-7
            
            # L1 normalize each descriptor
            descriptors = descriptors / (np.sum(descriptors, axis=1, keepdims=True) + eps)
            
            # Square root (Hellinger kernel approximation)
            descriptors = np.sqrt(descriptors + eps)
            
            # L2 normalize
            descriptors = descriptors / (np.linalg.norm(descriptors, axis=1, keepdims=True) + eps)
            
            # Statistical pooling: combine mean and std
            # This captures both central tendency and variance
            # which is more informative than max pooling
            mean_pool = np.mean(descriptors, axis=0)
            std_pool = np.std(descriptors, axis=0)
            
            # Concatenate mean and std (64 + 64 = 128)
            # If we have 128-dim descriptors, take first 64 dims for mean, last 64 for std
            half_dim = self.dimension // 2
            
            # Resize if needed
            if len(mean_pool) >= half_dim:
                mean_part = mean_pool[:half_dim]
                std_part = std_pool[:half_dim]
            else:
                mean_part = np.pad(mean_pool, (0, half_dim - len(mean_pool)))
                std_part = np.pad(std_pool, (0, half_dim - len(std_pool)))
            
            # Concatenate mean and std
            aggregated = np.concatenate([mean_part, std_part])
            
            # Ensure correct dimension
            if len(aggregated) < self.dimension:
                aggregated = np.pad(aggregated, (0, self.dimension - len(aggregated)))
            elif len(aggregated) > self.dimension:
                aggregated = aggregated[:self.dimension]
            
            # Final L2 normalization for cosine similarity
            norm = np.linalg.norm(aggregated)
            if norm > eps:
                aggregated = aggregated / norm
            
            return aggregated.astype(np.float32)
            
        except Exception as e:
            logger.error(f"SIFT extraction failed: {e}")
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
        'edge_histogram': EdgeHistogramExtractor(bins=64),
        'sift': SIFTExtractor(n_features=100, descriptor_size=128)
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
