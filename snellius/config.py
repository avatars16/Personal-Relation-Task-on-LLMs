"""
Configuration management for Snellius LLM processing
"""
import argparse
import os
from typing import List, Dict, Any


class Config:
    """Configuration class to manage all parameters"""
    
    def __init__(self):
        self.models: List[str] = ["meta-llama/Llama-3.3-70B-Instruct"]
        self.batch_size: int = 1
        self.save_frequency: int = 10
        self.input_file: str = ""
        self.output_dir: str = ""
        self.log_dir: str = ""
        self.gpu_monitor_interval: float = 10.0
        self.hf_token: str = ""
        self.output_format: str = "both"  # "csv", "excel", "both"
        self.max_length: int = 1000
        self.temperature: float = 0.7
    
    @classmethod
    def from_args(cls) -> 'Config':
        """Create configuration from command line arguments"""
        parser = argparse.ArgumentParser(
            description="Run LLM inference on Snellius cluster",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        # Model configuration
        parser.add_argument(
            '--models', 
            nargs='+', 
            default=["meta-llama/Llama-3.3-70B-Instruct"],
            help='List of HuggingFace model names to use'
        )
        
        # Processing configuration
        parser.add_argument(
            '--batch-size', 
            type=int, 
            default=1,
            help='Batch size for processing prompts'
        )
        
        parser.add_argument(
            '--save-frequency', 
            type=int, 
            default=10,
            help='How often to save results (number of questions)'
        )
        
        # File paths
        parser.add_argument(
            '--input-file', 
            type=str, 
            required=True,
            help='Path to input Excel file with prompts'
        )
        
        parser.add_argument(
            '--output-dir', 
            type=str, 
            default=None,
            help='Directory for output files (default: ./results)'
        )
        
        parser.add_argument(
            '--log-dir', 
            type=str, 
            default=None,
            help='Directory for log files (default: ./logs)'
        )
        
        # GPU monitoring
        parser.add_argument(
            '--gpu-monitor-interval', 
            type=float, 
            default=10.0,
            help='GPU monitoring interval in seconds'
        )
        
        # HuggingFace token
        parser.add_argument(
            '--hf-token', 
            type=str, 
            help='HuggingFace token for model access'
        )
        
        # Output format
        parser.add_argument(
            '--output-format', 
            choices=['csv', 'excel', 'both'], 
            default='both',
            help='Output file format'
        )
        
        # Generation parameters
        parser.add_argument(
            '--max-length', 
            type=int, 
            default=1000,
            help='Maximum length for text generation'
        )
        
        parser.add_argument(
            '--temperature', 
            type=float, 
            default=0.7,
            help='Temperature for text generation'
        )
        
        args = parser.parse_args()
        
        # Create config instance
        config = cls()
        config.models = args.models
        config.batch_size = args.batch_size
        config.save_frequency = args.save_frequency
        config.input_file = args.input_file
        config.hf_token = args.hf_token
        config.output_format = args.output_format
        config.max_length = args.max_length
        config.temperature = args.temperature
        config.gpu_monitor_interval = args.gpu_monitor_interval
        
        # Set default paths if not provided
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config.output_dir = args.output_dir or os.path.join(script_dir, "results")
        config.log_dir = args.log_dir or os.path.join(script_dir, "logs")
        
        # Create directories
        os.makedirs(config.output_dir, exist_ok=True)
        os.makedirs(config.log_dir, exist_ok=True)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'models': self.models,
            'batch_size': self.batch_size,
            'save_frequency': self.save_frequency,
            'input_file': self.input_file,
            'output_dir': self.output_dir,
            'log_dir': self.log_dir,
            'gpu_monitor_interval': self.gpu_monitor_interval,
            'hf_token': self.hf_token,
            'output_format': self.output_format,
            'max_length': self.max_length,
            'temperature': self.temperature,
        }
    
    def __repr__(self) -> str:
        """String representation of configuration"""
        return f"Config({self.to_dict()})"
