"""
Utilities for general-purpose LLM processing on Snellius
This module contains reusable utility functions
"""
import os
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def setup_logging(log_dir: str, log_level: str = "INFO") -> None:
    """Set up logging configuration
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"snellius_processing_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    
    logger.info(f"Logging initialized. Log file: {log_file}")


def validate_file_path(file_path: str, must_exist: bool = True) -> bool:
    """Validate a file path
    
    Args:
        file_path: Path to validate
        must_exist: Whether the file must already exist
        
    Returns:
        True if valid, False otherwise
    """
    if not file_path:
        logger.error("File path is empty")
        return False
    
    if must_exist and not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False
    
    # Check if directory exists for output files
    if not must_exist:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by replacing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscores or dashes
    invalid_chars = [':', '/', '\\', '<', '>', '"', '|', '?', '*']
    sanitized = filename
    
    for char in invalid_chars:
        if char == '/':
            sanitized = sanitized.replace(char, '-')
        else:
            sanitized = sanitized.replace(char, '_')
    
    return sanitized


def format_model_name_for_output(model_name: str) -> str:
    """Format model name for use in output filenames
    
    Args:
        model_name: Original model name
        
    Returns:
        Formatted model name safe for filenames
    """
    return sanitize_filename(model_name)


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage information
    
    Returns:
        Dictionary with memory usage information
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            'percent': process.memory_percent()
        }
    except ImportError:
        logger.warning("psutil not available. Memory monitoring disabled.")
        return {}
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return {}


def estimate_batch_size(available_memory_gb: float, model_size_gb: float) -> int:
    """Estimate optimal batch size based on available memory
    
    Args:
        available_memory_gb: Available GPU memory in GB
        model_size_gb: Estimated model size in GB
        
    Returns:
        Recommended batch size
    """
    # Simple heuristic: use 70% of available memory for batching
    # Assumes each token in batch uses roughly similar memory
    usable_memory = available_memory_gb * 0.7
    memory_per_sample = model_size_gb * 0.1  # Rough estimate
    
    batch_size = max(1, int(usable_memory / memory_per_sample))
    logger.info(f"Estimated batch size: {batch_size} (available: {available_memory_gb}GB, model: {model_size_gb}GB)")
    
    return batch_size


def create_result_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a summary of processing results
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Summary dictionary
    """
    if not results:
        return {"total_results": 0}
    
    total_duration = sum(r.get('duration', 0) for r in results)
    total_input_tokens = sum(r.get('input_tokens', 0) for r in results)
    total_output_tokens = sum(r.get('output_tokens', 0) for r in results)
    total_tokens = sum(r.get('total_tokens', 0) for r in results)
    
    # Count unique models, representations, approaches
    models = set(r.get('Model', 'unknown') for r in results)
    representations = set(r.get('Representation', 'unknown') for r in results)
    approaches = set(r.get('Approach', 'unknown') for r in results)
    
    return {
        "total_results": len(results),
        "total_duration_seconds": total_duration,
        "average_duration_seconds": total_duration / len(results) if results else 0,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
        "average_tokens_per_result": total_tokens / len(results) if results else 0,
        "unique_models": list(models),
        "unique_representations": list(representations),
        "unique_approaches": list(approaches),
        "tokens_per_second": total_tokens / total_duration if total_duration > 0 else 0
    }
