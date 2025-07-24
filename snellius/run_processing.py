"""
Main execution script for Snellius LLM processing
This script provides a clean interface with command-line arguments
"""
import sys
import os
import logging
from typing import List

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core.llm_engine import LLMEngine
from data.processors import ExcelQuestionProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('snellius_processing.log')
    ]
)
logger = logging.getLogger(__name__)


def run_processing(config: Config) -> None:
    """Run the main processing pipeline
    
    Args:
        config: Configuration object with all parameters
    """
    logger.info("Starting Snellius LLM processing")
    logger.info(f"Configuration: {config}")
    
    # Initialize data processor
    processor = ExcelQuestionProcessor()
    
    # Load input data
    try:
        data = processor.load_data(config.input_file)
        logger.info(f"Successfully loaded input file: {config.input_file}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return
    
    # Process each model
    for model_name in config.models:
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing with model: {model_name}")
        logger.info(f"{'='*50}")
        
        # Initialize LLM engine
        llm_engine = LLMEngine(
            hf_token=config.hf_token,
            log_dir=config.log_dir,
            gpu_monitor_interval=config.gpu_monitor_interval
        )
        
        # Load model
        success = llm_engine.load_model(model_name)
        if not success:
            logger.error(f"Failed to load model {model_name}. Skipping...")
            continue
        
        try:
            # Create a copy of config with current model for processing
            model_config = Config()
            model_config.__dict__.update(config.__dict__)
            model_config.models = [model_name]
            
            # Process data
            results = processor.process_data(data, llm_engine, model_config)
            logger.info(f"Processing completed for {model_name}. Processed {len(results)} items.")
            
        except Exception as e:
            logger.error(f"Error during processing with model {model_name}: {e}")
            
        finally:
            # Clean up resources
            if llm_engine.is_model_loaded():
                llm_engine.unload_model()
                logger.info(f"Model {model_name} unloaded successfully")
    
    logger.info("All processing completed!")


def main():
    """Main entry point"""
    try:
        # Load configuration from command line arguments
        config = Config.from_args()
        
        # Run processing
        run_processing(config)
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
