# Snellius LLM Processing

A modular framework for running LLM inference on the Snellius cluster with configurable parameters and reusable components.

## Structure

```
snellius/
├── config.py              # Configuration management with argparse
├── run_processing.py       # Main entry point
├── gpu_monitor.py         # GPU monitoring (unchanged)
├── requirements.txt       # Dependencies
├── core/                  # Reusable LLM execution engine
│   ├── __init__.py
│   └── llm_engine.py     # Core LLM functionality
├── data/                  # Data processing modules
│   ├── __init__.py
│   └── processors.py     # Excel question processor
└── utils/                 # Utility functions
    ├── __init__.py
    └── helpers.py         # General utility functions
```

## Features

- **Configurable via command line arguments**: batch size, save frequency, models, file locations
- **Modular design**: Clear separation between core LLM engine and data-specific processing
- **Reusable components**: Core engine can be used for different data types and projects
- **GPU monitoring**: Integrated GPU usage tracking
- **Resume capability**: Automatically detects and skips previously processed questions
- **Multiple output formats**: CSV, Excel, or both
- **Batch processing**: Configurable batch sizes with automatic optimization

## Usage

### Basic Usage

```bash
python run_processing.py --input-file /path/to/questions.xlsx --output-dir ./results
```

### Advanced Usage

```bash
python run_processing.py \
    --input-file /path/to/questions.xlsx \
    --output-dir ./results \
    --models meta-llama/Llama-3.3-70B-Instruct microsoft/DialoGPT-medium \
    --batch-size 4 \
    --save-frequency 20 \
    --gpu-monitor-interval 5.0 \
    --output-format csv \
    --max-length 1500 \
    --temperature 0.8
```

### Command Line Arguments

- `--input-file`: Path to input Excel file with prompts (required)
- `--output-dir`: Directory for output files (default: ./results)
- `--log-dir`: Directory for log files (default: ./logs)
- `--models`: List of HuggingFace model names (default: meta-llama/Llama-3.3-70B-Instruct)
- `--batch-size`: Batch size for processing prompts (default: 1)
- `--save-frequency`: How often to save results (default: 10)
- `--gpu-monitor-interval`: GPU monitoring interval in seconds (default: 10.0)
- `--hf-token`: HuggingFace token for model access
- `--output-format`: Output format - csv, excel, or both (default: both)
- `--max-length`: Maximum length for text generation (default: 1000)
- `--temperature`: Temperature for text generation (default: 0.7)

## Extending the Framework

### Adding New Data Processors

To process different data formats, create a new processor class:

```python
from data.processors import DataProcessor

class MyCustomProcessor(DataProcessor):
    def load_data(self, file_path: str):
        # Load your custom data format
        pass

    def process_data(self, data, llm_engine, config):
        # Process data using the LLM engine
        pass

    def save_results(self, results, output_path, output_format="both"):
        # Save results in your desired format
        pass
```

### Using the Core LLM Engine

The core LLM engine can be used independently:

```python
from core.llm_engine import LLMEngine

# Initialize engine
engine = LLMEngine(hf_token="your_token", log_dir="./logs")

# Load model
engine.load_model("meta-llama/Llama-3.3-70B-Instruct")

# Generate single response
result = engine.generate_response("Your prompt here")

# Generate batch responses
results = engine.batch_generate(["Prompt 1", "Prompt 2", "Prompt 3"])

# Clean up
engine.unload_model()
```

## Requirements

See `requirements.txt` for all dependencies. Key requirements:

- torch
- transformers
- pandas
- tqdm
- pynvml (for GPU monitoring)

## GPU Monitoring

GPU monitoring is automatically enabled and logs to CSV files in the log directory. Monitoring tracks:

- GPU utilization
- Memory usage
- Processing duration
- Batch performance metrics
