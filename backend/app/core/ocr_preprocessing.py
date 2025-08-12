"""
OCR Preprocessing for Scanned Documents with Quality Validation

This module provides advanced OCR preprocessing capabilities for scanned documents,
including image enhancement, OCR quality assessment, and comprehensive validation
for the Data Normalization Layer Foundation.
"""

import io
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import pytesseract
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class ImageQuality(str, Enum):
    """Image quality assessment levels"""
    EXCELLENT = "excellent"  # 90-100% - High contrast, clear text, good resolution
    GOOD = "good"           # 70-89% - Clear text, minor issues
    FAIR = "fair"           # 50-69% - Readable text, some quality issues
    POOR = "poor"           # <50% - Difficult to read, significant issues


class OCRConfidence(str, Enum):
    """OCR confidence levels"""
    HIGH = "high"      # 90-100% - Very confident in text extraction
    MEDIUM = "medium"   # 70-89% - Moderately confident
    LOW = "low"         # 50-69% - Low confidence, may have errors
    UNCERTAIN = "uncertain"  # <50% - Very low confidence, likely errors


@dataclass
class ImagePreprocessingResult:
    """Result of image preprocessing operations"""
    original_image: Image.Image
    processed_image: Image.Image
    preprocessing_steps: List[str] = field(default_factory=list)
    quality_improvement: float = 0.0  # Percentage improvement
    processing_duration: float = 0.0  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OCRResult:
    """Result of OCR processing with quality metrics"""
    extracted_text: str
    confidence_score: int  # 0-100
    confidence_level: OCRConfidence
    image_quality: ImageQuality
    image_quality_score: int  # 0-100
    ocr_quality_score: int  # 0-100
    processing_duration: float  # seconds
    preprocessing_applied: List[str] = field(default_factory=list)
    quality_indicators: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class OCRPreprocessor:
    """
    Advanced OCR preprocessor with image enhancement and quality validation
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # OCR configuration
        self.ocr_config = '--oem 3 --psm 6'  # LSTM OCR Engine + Uniform block of text
        
        # Image enhancement parameters
        self.enhancement_params = {
            'contrast': 1.5,      # Contrast enhancement factor
            'brightness': 1.2,    # Brightness enhancement factor
            'sharpness': 1.3,    # Sharpness enhancement factor
            'denoise': True,      # Enable denoising
            'deskew': True,       # Enable automatic deskewing
            'binarization': True  # Enable adaptive binarization
        }
    
    async def preprocess_and_ocr(
        self, 
        image_bytes: bytes,
        filename: str = None,
        apply_enhancement: bool = True,
        validate_quality: bool = True
    ) -> OCRResult:
        """
        Complete OCR preprocessing pipeline with quality validation
        """
        start_time = datetime.utcnow()
        
        try:
            # Load and analyze original image
            original_image = Image.open(io.BytesIO(image_bytes))
            original_quality = self._assess_image_quality(original_image)
            
            # Apply preprocessing if requested
            if apply_enhancement:
                preprocessing_result = await self._preprocess_image(original_image)
                processed_image = preprocessing_result.processed_image
                preprocessing_steps = preprocessing_result.preprocessing_steps
            else:
                processed_image = original_image
                preprocessing_steps = []
            
            # Perform OCR
            ocr_text, ocr_confidence = self._perform_ocr(processed_image)
            
            # Assess OCR quality
            ocr_quality = self._assess_ocr_quality(ocr_text, ocr_confidence, processed_image)
            
            # Calculate processing duration
            processing_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Generate quality indicators
            quality_indicators = self._generate_quality_indicators(
                original_image, processed_image, original_quality, ocr_quality
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                original_quality, ocr_quality, preprocessing_steps
            )
            
            # Create OCR result
            result = OCRResult(
                extracted_text=ocr_text,
                confidence_score=ocr_confidence,
                confidence_level=self._get_confidence_level(ocr_confidence),
                image_quality=original_quality,
                image_quality_score=self._get_quality_score(original_quality),
                ocr_quality_score=ocr_quality,
                processing_duration=processing_duration,
                preprocessing_applied=preprocessing_steps,
                quality_indicators=quality_indicators,
                recommendations=recommendations,
                metadata={
                    'original_dimensions': f"{original_image.width}x{original_image.height}",
                    'original_mode': original_image.mode,
                    'filename': filename,
                    'ocr_config': self.ocr_config
                }
            )
            
            # Validate quality if requested
            if validate_quality:
                await self._validate_ocr_quality(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"OCR preprocessing failed: {e}")
            # Return error result
            return OCRResult(
                extracted_text="[OCR processing failed]",
                confidence_score=0,
                confidence_level=OCRConfidence.UNCERTAIN,
                image_quality=ImageQuality.POOR,
                image_quality_score=0,
                ocr_quality_score=0,
                processing_duration=(datetime.utcnow() - start_time).total_seconds(),
                issues=[f"Processing error: {str(e)}"],
                recommendations=["Check image format and try again", "Verify image is not corrupted"]
            )
    
    async def _preprocess_image(self, image: Image.Image) -> ImagePreprocessingResult:
        """Apply comprehensive image preprocessing"""
        start_time = datetime.utcnow()
        original_image = image.copy()
        processed_image = image.copy()
        steps = []
        
        try:
            # Convert to RGB if needed
            if processed_image.mode != 'RGB':
                processed_image = processed_image.convert('RGB')
                steps.append("converted_to_rgb")
            
            # Convert to numpy array for OpenCV operations
            img_array = np.array(processed_image)
            
            # Apply denoising if enabled
            if self.enhancement_params['denoise']:
                img_array = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
                steps.append("denoised")
            
            # Apply deskewing if enabled
            if self.enhancement_params['deskew']:
                img_array = self._deskew_image(img_array)
                steps.append("deskewed")
            
            # Apply adaptive binarization if enabled
            if self.enhancement_params['binarization']:
                img_array = self._apply_adaptive_binarization(img_array)
                steps.append("binarized")
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(img_array)
            
            # Apply PIL-based enhancements
            processed_image = self._apply_pil_enhancements(processed_image)
            steps.extend(["contrast_enhanced", "brightness_enhanced", "sharpness_enhanced"])
            
            # Calculate quality improvement
            original_quality = self._assess_image_quality(original_image)
            processed_quality = self._assess_image_quality(processed_image)
            quality_improvement = self._calculate_quality_improvement(original_quality, processed_quality)
            
            processing_duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ImagePreprocessingResult(
                original_image=original_image,
                processed_image=processed_image,
                preprocessing_steps=steps,
                quality_improvement=quality_improvement,
                processing_duration=processing_duration,
                metadata={
                    'enhancement_params': self.enhancement_params,
                    'quality_improvement': quality_improvement
                }
            )
            
        except Exception as e:
            self.logger.warning(f"Image preprocessing failed: {e}")
            # Return original image if preprocessing fails
            return ImagePreprocessingResult(
                original_image=original_image,
                processed_image=original_image,
                preprocessing_steps=steps + ["preprocessing_failed"],
                quality_improvement=0.0,
                processing_duration=(datetime.utcnow() - start_time).total_seconds(),
                metadata={'error': str(e)}
            )
    
    def _deskew_image(self, img_array: np.ndarray) -> np.ndarray:
        """Automatically deskew the image"""
        try:
            # Convert to grayscale for deskewing
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Find edges
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                # Calculate the average angle
                angles = []
                for rho, theta in lines[:10]:  # Use first 10 lines
                    angle = theta * 180 / np.pi
                    if angle < 45:
                        angles.append(angle)
                    elif angle > 135:
                        angles.append(angle - 180)
                
                if angles:
                    avg_angle = np.mean(angles)
                    
                    # Rotate the image
                    if abs(avg_angle) > 0.5:  # Only rotate if angle is significant
                        height, width = img_array.shape[:2]
                        center = (width // 2, height // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                        img_array = cv2.warpAffine(img_array, rotation_matrix, (width, height))
            
            return img_array
            
        except Exception as e:
            self.logger.warning(f"Deskewing failed: {e}")
            return img_array
    
    def _apply_adaptive_binarization(self, img_array: np.ndarray) -> np.ndarray:
        """Apply adaptive binarization for better text extraction"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to RGB
            return cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
            
        except Exception as e:
            self.logger.warning(f"Binarization failed: {e}")
            return img_array
    
    def _apply_pil_enhancements(self, image: Image.Image) -> Image.Image:
        """Apply PIL-based image enhancements"""
        try:
            # Enhance contrast
            contrast_enhancer = ImageEnhance.Contrast(image)
            image = contrast_enhancer.enhance(self.enhancement_params['contrast'])
            
            # Enhance brightness
            brightness_enhancer = ImageEnhance.Brightness(image)
            image = brightness_enhancer.enhance(self.enhancement_params['brightness'])
            
            # Enhance sharpness
            sharpness_enhancer = ImageEnhance.Sharpness(image)
            image = sharpness_enhancer.enhance(self.enhancement_params['sharpness'])
            
            return image
            
        except Exception as e:
            self.logger.warning(f"PIL enhancements failed: {e}")
            return image
    
    def _perform_ocr(self, image: Image.Image) -> Tuple[str, int]:
        """Perform OCR on the image"""
        try:
            # Use pytesseract with custom configuration
            text = pytesseract.image_to_string(
                image, 
                config=self.ocr_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and confidence
            if isinstance(text, dict) and 'text' in text:
                extracted_text = text['text']
                # Calculate average confidence from all words
                confidences = [int(conf) for conf in text.get('conf', []) if conf != -1]
                avg_confidence = int(np.mean(confidences)) if confidences else 0
            else:
                extracted_text = str(text)
                avg_confidence = 50  # Default confidence for string output
            
            return extracted_text.strip(), avg_confidence
            
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return "[OCR processing failed]", 0
    
    def _assess_image_quality(self, image: Image.Image) -> ImageQuality:
        """Assess the quality of the image for OCR processing"""
        try:
            # Convert to grayscale for analysis
            gray = image.convert('L')
            img_array = np.array(gray)
            
            # Calculate various quality metrics
            metrics = {}
            
            # Contrast (standard deviation of pixel values)
            metrics['contrast'] = np.std(img_array)
            
            # Brightness (mean pixel value)
            metrics['brightness'] = np.mean(img_array)
            
            # Sharpness (Laplacian variance)
            laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
            metrics['sharpness'] = laplacian.var()
            
            # Noise estimation (using high-frequency components)
            f_transform = np.fft.fft2(img_array)
            f_shift = np.fft.fftshift(f_transform)
            high_freq = np.abs(f_shift[img_array.shape[0]//4:, img_array.shape[1]//4:])
            metrics['noise'] = np.mean(high_freq)
            
            # Calculate overall quality score
            quality_score = self._calculate_image_quality_score(metrics)
            
            # Map to quality level
            if quality_score >= 90:
                return ImageQuality.EXCELLENT
            elif quality_score >= 70:
                return ImageQuality.GOOD
            elif quality_score >= 50:
                return ImageQuality.FAIR
            else:
                return ImageQuality.POOR
                
        except Exception as e:
            self.logger.warning(f"Image quality assessment failed: {e}")
            return ImageQuality.POOR
    
    def _calculate_image_quality_score(self, metrics: Dict[str, float]) -> int:
        """Calculate overall image quality score from metrics"""
        try:
            # Normalize metrics to 0-100 scale
            normalized_metrics = {}
            
            # Contrast: Higher is better, normalize to 0-100
            normalized_metrics['contrast'] = min(100, max(0, metrics['contrast'] / 50))
            
            # Brightness: Optimal around 128, penalize extremes
            brightness_score = 100 - abs(metrics['brightness'] - 128) / 128 * 100
            normalized_metrics['brightness'] = max(0, brightness_score)
            
            # Sharpness: Higher is better, normalize to 0-100
            normalized_metrics['sharpness'] = min(100, max(0, metrics['sharpness'] / 1000))
            
            # Noise: Lower is better, invert and normalize
            noise_score = max(0, 100 - metrics['noise'] / 100)
            normalized_metrics['noise'] = noise_score
            
            # Weighted average
            weights = {'contrast': 0.3, 'brightness': 0.2, 'sharpness': 0.3, 'noise': 0.2}
            total_score = sum(normalized_metrics[key] * weights[key] for key in weights)
            
            return int(total_score)
            
        except Exception as e:
            self.logger.warning(f"Quality score calculation failed: {e}")
            return 50  # Default score
    
    def _assess_ocr_quality(self, text: str, confidence: int, image: Image.Image) -> int:
        """Assess the quality of OCR results"""
        try:
            # Base score from OCR confidence
            base_score = confidence
            
            # Text length factor (longer text generally means better extraction)
            text_length_factor = min(100, len(text) / 100 * 50)  # Cap at 50 points
            
            # Text quality indicators
            quality_indicators = 0
            
            # Check for common OCR artifacts
            if text and len(text.strip()) > 0:
                # Penalize for excessive special characters (OCR artifacts)
                special_char_ratio = sum(1 for c in text if c in '!@#$%^&*()_+-=[]{}|;:,.<>?') / len(text)
                if special_char_ratio < 0.1:  # Less than 10% special chars
                    quality_indicators += 20
                elif special_char_ratio < 0.2:
                    quality_indicators += 10
                
                # Reward for proper word spacing
                if '  ' not in text:  # No double spaces
                    quality_indicators += 15
                
                # Reward for mixed case (indicates good character recognition)
                if any(c.isupper() for c in text) and any(c.islower() for c in text):
                    quality_indicators += 15
                
                # Reward for numbers (often important in documents)
                if any(c.isdigit() for c in text):
                    quality_indicators += 10
            
            # Calculate final score
            final_score = int((base_score + text_length_factor + quality_indicators) / 3)
            
            return max(0, min(100, final_score))
            
        except Exception as e:
            self.logger.warning(f"OCR quality assessment failed: {e}")
            return confidence  # Return base confidence
    
    def _get_confidence_level(self, confidence: int) -> OCRConfidence:
        """Convert confidence score to confidence level"""
        if confidence >= 90:
            return OCRConfidence.HIGH
        elif confidence >= 70:
            return OCRConfidence.MEDIUM
        elif confidence >= 50:
            return OCRConfidence.LOW
        else:
            return OCRConfidence.UNCERTAIN
    
    def _get_quality_score(self, quality: ImageQuality) -> int:
        """Convert quality enum to numeric score"""
        quality_scores = {
            ImageQuality.EXCELLENT: 95,
            ImageQuality.GOOD: 80,
            ImageQuality.FAIR: 60,
            ImageQuality.POOR: 30
        }
        return quality_scores.get(quality, 50)
    
    def _generate_quality_indicators(
        self, 
        original_image: Image.Image, 
        processed_image: Image.Image, 
        original_quality: ImageQuality, 
        ocr_quality: int
    ) -> Dict[str, Any]:
        """Generate comprehensive quality indicators"""
        return {
            'original_dimensions': f"{original_image.width}x{original_image.height}",
            'original_mode': original_image.mode,
            'original_quality': original_quality.value,
            'processed_dimensions': f"{processed_image.width}x{processed_image.height}",
            'processed_mode': processed_image.mode,
            'ocr_quality': ocr_quality,
            'enhancement_applied': original_image != processed_image,
            'quality_metrics': {
                'contrast': self._calculate_contrast_metric(processed_image),
                'brightness': self._calculate_brightness_metric(processed_image),
                'sharpness': self._calculate_sharpness_metric(processed_image)
            }
        }
    
    def _calculate_contrast_metric(self, image: Image.Image) -> float:
        """Calculate contrast metric for the image"""
        try:
            gray = image.convert('L')
            img_array = np.array(gray)
            return float(np.std(img_array))
        except:
            return 0.0
    
    def _calculate_brightness_metric(self, image: Image.Image) -> float:
        """Calculate brightness metric for the image"""
        try:
            gray = image.convert('L')
            img_array = np.array(gray)
            return float(np.mean(img_array))
        except:
            return 0.0
    
    def _calculate_sharpness_metric(self, image: Image.Image) -> float:
        """Calculate sharpness metric for the image"""
        try:
            gray = image.convert('L')
            img_array = np.array(gray)
            laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
            return float(laplacian.var())
        except:
            return 0.0
    
    def _generate_recommendations(
        self, 
        image_quality: ImageQuality, 
        ocr_quality: int, 
        preprocessing_steps: List[str]
    ) -> List[str]:
        """Generate recommendations based on quality assessment"""
        recommendations = []
        
        # Image quality recommendations
        if image_quality == ImageQuality.POOR:
            recommendations.extend([
                "Image quality is poor - consider rescanning at higher resolution",
                "Check scanner settings for better contrast and brightness",
                "Ensure proper lighting during scanning"
            ])
        elif image_quality == ImageQuality.FAIR:
            recommendations.extend([
                "Image quality could be improved for better OCR results",
                "Consider applying additional preprocessing steps"
            ])
        
        # OCR quality recommendations
        if ocr_quality < 50:
            recommendations.extend([
                "OCR quality is very low - manual review recommended",
                "Consider preprocessing the image before OCR",
                "Check if the document contains handwritten text"
            ])
        elif ocr_quality < 70:
            recommendations.extend([
                "OCR quality is moderate - review extracted text for accuracy",
                "Consider manual correction of critical information"
            ])
        
        # Preprocessing recommendations
        if not preprocessing_steps:
            recommendations.append("Consider applying image preprocessing for better results")
        elif "preprocessing_failed" in preprocessing_steps:
            recommendations.append("Image preprocessing failed - check image format and try again")
        
        return recommendations
    
    def _calculate_quality_improvement(
        self, 
        original_quality: ImageQuality, 
        processed_quality: ImageQuality
    ) -> float:
        """Calculate quality improvement percentage"""
        try:
            original_score = self._get_quality_score(original_quality)
            processed_score = self._get_quality_score(processed_quality)
            
            if original_score == 0:
                return 0.0
            
            improvement = ((processed_score - original_score) / original_score) * 100
            return max(0.0, improvement)
            
        except Exception as e:
            self.logger.warning(f"Quality improvement calculation failed: {e}")
            return 0.0
    
    async def _validate_ocr_quality(self, result: OCRResult) -> None:
        """Validate OCR quality and add issues if needed"""
        issues = []
        
        # Check for very low OCR quality
        if result.ocr_quality_score < 30:
            issues.append("OCR quality is critically low - manual review required")
        
        # Check for empty or very short text
        if len(result.extracted_text.strip()) < 10:
            issues.append("Extracted text is very short - may indicate OCR failure")
        
        # Check for excessive special characters
        if result.extracted_text:
            special_char_ratio = sum(1 for c in result.extracted_text if c in '!@#$%^&*()_+-=[]{}|;:,.<>?') / len(result.extracted_text)
            if special_char_ratio > 0.3:  # More than 30% special chars
                issues.append("High ratio of special characters detected - possible OCR artifacts")
        
        # Check for image quality issues
        if result.image_quality == ImageQuality.POOR:
            issues.append("Image quality is poor - may affect OCR accuracy")
        
        # Add issues to result
        result.issues.extend(issues)
