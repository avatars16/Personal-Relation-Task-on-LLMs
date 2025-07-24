"""
Core LLM execution engine for Snellius cluster
This module provides a generic interface for running LLM inference
"""
import os
import time
import torch
import warnings
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from gpu_monitor import GPUMonitor
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMEngine:
    """Core LLM execution engine"""
    
    def __init__(self, hf_token: str, log_dir: Optional[str] = None, gpu_monitor_interval: float = 2.0):
        """Initialize the LLM Engine
        
        Args:
            hf_token: HuggingFace authentication token
            log_dir: Directory for GPU monitoring logs
            gpu_monitor_interval: Interval for GPU monitoring in seconds
        """
        # Set environment variables for CUDA optimization
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        
        self.hf_token = hf_token
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        # Initialize GPU monitoring
        self.gpu_monitor = GPUMonitor(monitor_interval=gpu_monitor_interval, log_dir=log_dir)
        
        logger.info(f"LLM Engine initialized. Using device: {self.device}")
        if os.environ.get('HF_HOME'):
            logger.info(f"HF_HOME is set to: {os.environ['HF_HOME']}")

    def load_model(self, model_name: str, use_8bit: bool = True, use_flash_attention: bool = True) -> bool:
        """Load a HuggingFace model and tokenizer
        
        Args:
            model_name: Name of the HuggingFace model to load
            use_8bit: Whether to use 8-bit quantization
            use_flash_attention: Whether to use flash attention 2
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        self.model_name = model_name
        
        try:
            logger.info(f"Loading tokenizer for {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, token=self.hf_token)
            
            # Set padding tokens to avoid warnings
            self.tokenizer.padding_side = "left" 
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Log GPU state before loading model
            self.gpu_monitor.log_gpu_metrics(log_to_csv=True, description="pre_model_load")
            logger.info(f"Loading model {self.model_name}...")
            
            # Start continuous GPU monitoring during model loading
            self.gpu_monitor.start_monitoring(log_to_csv=True, description="model_loading")
            
            # Configure quantization if requested
            model_kwargs = {
                "torch_dtype": torch.float16,
                "device_map": "auto",
                "token": self.hf_token
            }
            
            if use_8bit:
                bnb_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_enable_fp32_cpu_offload=True,
                )
                model_kwargs["quantization_config"] = bnb_config
            
            if use_flash_attention:
                model_kwargs["attn_implementation"] = "flash_attention_2"
            
            # Load the model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name, 
                **model_kwargs
            ).eval()
            
            # Stop monitoring after model load
            self.gpu_monitor.stop_monitoring()
            
            # Log GPU state after loading and save summary
            logger.info("GPU state after model loading:")
            self.gpu_monitor.log_gpu_metrics(log_to_csv=True, description="post_model_load")
            self.gpu_monitor.save_summary_to_csv(description="model_loading_summary")
            
            logger.info(f"Model {self.model_name} loaded successfully!")
            return True
            
        except Exception as e:
            self.gpu_monitor.stop_monitoring()
            logger.error(f"Error loading model {self.model_name}: {str(e)}")
            return False

    def generate_response(self, prompt_text: str, max_length: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
        """Generate a response from the loaded model
        
        Args:
            prompt_text: Input prompt text
            max_length: Maximum length of generated text
            temperature: Temperature for generation
            
        Returns:
            Dictionary containing response, duration, and token counts
        """
        if not self.model or not self.tokenizer:
            return {
                "prompt": prompt_text,
                "response": "Model not loaded",
                "duration": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
        
        start_time = time.time()
        
        try:
            # Generate a unique identifier for this inference
            inference_id = f"inference_{int(start_time)}"
            
            # Log GPU state before inference
            self.gpu_monitor.log_gpu_metrics(log_to_csv=True, description=f"{inference_id}_pre")
            
            # Start monitoring during inference
            self.gpu_monitor.start_monitoring(log_to_csv=True, description=inference_id)
            
            # Tokenize input and count input tokens
            inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.device)
            input_tokens_count = len(inputs.input_ids[0])
            
            # Generate response
            with torch.no_grad():
                output = self.model.generate(**inputs, max_length=max_length, temperature=temperature)
            
            # Count output tokens (excluding input tokens)
            output_tokens_count = len(output[0]) - input_tokens_count
            total_tokens = input_tokens_count + output_tokens_count
            
            # Decode the output
            generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
            
            # Stop monitoring
            self.gpu_monitor.stop_monitoring()
            
            # Log GPU state after inference
            self.gpu_monitor.log_gpu_metrics(log_to_csv=True, description=f"{inference_id}_post")
            
            duration = time.time() - start_time
            logger.info(f"Generation took {duration:.2f} seconds")
            logger.info(f"Input tokens: {input_tokens_count}, Output tokens: {output_tokens_count}, Total: {total_tokens}")
            
            # Save summary to CSV
            self.gpu_monitor.save_summary_to_csv(description=f"{inference_id}_summary")
            
            return {
                "prompt": prompt_text,
                "response": generated_text,
                "duration": duration,
                "input_tokens": input_tokens_count,
                "output_tokens": output_tokens_count,
                "total_tokens": total_tokens
            }
            
        except Exception as e:
            self.gpu_monitor.stop_monitoring()
            duration = time.time() - start_time
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            return {
                "prompt": prompt_text,
                "response": error_msg,
                "duration": duration,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }

    def batch_generate(self, prompts: List[str], max_length: int = 1000, temperature: float = 0.7) -> List[Dict[str, Any]]:
        """Generate responses for a batch of prompts
        
        Args:
            prompts: List of prompt texts
            max_length: Maximum length of generated text
            temperature: Temperature for generation
            
        Returns:
            List of dictionaries containing response, duration, and token counts for each prompt
        """
        if not self.model or not self.tokenizer:
            return [{
                "prompt": prompt,
                "response": "Model not loaded",
                "duration": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            } for prompt in prompts]

        start_time = time.time()
        batch_id = f"batch_{int(start_time)}"
        results = []

        # Log GPU state before batch processing
        logger.info(f"GPU state before batch processing ({len(prompts)} prompts):")
        self.gpu_monitor.log_gpu_metrics(log_to_csv=True, description=f"{batch_id}_pre")

        # Start monitoring for the entire batch
        self.gpu_monitor.start_monitoring(log_to_csv=True, description=batch_id)

        try:
            prompt_start = time.time()

            encoding = self.tokenizer(
                prompts, padding=True, return_tensors='pt', truncation=True
            ).to(self.device)

            # Generate response
            with torch.no_grad():
                output = self.model.generate(
                    **encoding,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            prompt_duration = time.time() - prompt_start

            # Stop monitoring
            self.gpu_monitor.stop_monitoring()

            pad_token_id = self.tokenizer.pad_token_id

            for i, prompt_text in enumerate(prompts):
                # Accurate Token Counting and Response Extraction
                attention_mask = encoding.attention_mask[i]
                output_sequence = output[i]

                # Get actual input token count (excluding padding)
                input_tokens_count = attention_mask.sum().item()

                # Slice the output tensor to get potentially generated IDs
                generated_ids_with_padding = output_sequence[input_tokens_count:]

                # Count actual generated tokens (excluding padding)
                actual_generated_ids = generated_ids_with_padding
                if pad_token_id is not None:
                    # Find indices of pad tokens in the generated part
                    pad_indices = (generated_ids_with_padding == pad_token_id).nonzero(as_tuple=False)
                    if len(pad_indices) > 0:
                        first_pad_index = pad_indices[0][0].item()
                        actual_generated_ids = generated_ids_with_padding[:first_pad_index]

                output_tokens_count = len(actual_generated_ids)
                total_tokens = input_tokens_count + output_tokens_count

                # Decode the actual generated response, not the prompt
                response_text = self.tokenizer.decode(
                    actual_generated_ids, skip_special_tokens=True
                )

                results.append({
                    "prompt": prompt_text,
                    "response": response_text,
                    "duration": prompt_duration,
                    "input_tokens": input_tokens_count,
                    "output_tokens": output_tokens_count,
                    "total_tokens": total_tokens
                })

            # Log GPU state after batch processing
            logger.info("GPU state after batch processing:")
            self.gpu_monitor.log_gpu_metrics(log_to_csv=True, description=f"{batch_id}_post")

            total_duration = time.time() - start_time
            logger.info(f"Batch processing completed in {total_duration:.2f} seconds")

            # Save batch summary to CSV
            self.gpu_monitor.save_summary_to_csv(description=f"{batch_id}_summary")

            return results

        except Exception as e:
            logger.error(f"Error during batch generation: {e}")
            # Ensure monitoring stops even if there's an error
            if self.gpu_monitor.is_monitoring():
                self.gpu_monitor.stop_monitoring()
            
            # Return error results
            error_result = {
                "prompt": "BATCH_ERROR",
                "response": f"Error: {e}",
                "duration": time.time() - start_time,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
            results.append(error_result)
            return results

    def unload_model(self) -> None:
        """Unload the model to free up GPU memory"""
        if self.model:
            # Check GPU state before unloading
            logger.info("GPU state before unloading model:")
            self.gpu_monitor.log_gpu_metrics(log_to_csv=True, description="pre_model_unload")
            
            del self.model
            del self.tokenizer
            torch.cuda.empty_cache()
            self.model = None
            self.tokenizer = None
            
            # Check GPU state after unloading
            logger.info("GPU state after unloading model:")
            self.gpu_monitor.log_gpu_metrics(log_to_csv=True, description="post_model_unload")
            logger.info(f"Model {self.model_name} unloaded and GPU memory cleared")

    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded"""
        return self.model is not None and self.tokenizer is not None
