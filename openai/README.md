# OpenAI Batch Processing

Tool for processing OpenAI batch requests from Excel files.

## Usage

The main script `batch_processor.py` handles the complete workflow with default paths:

### 1. Create batch request files from Excel (uses default Excel path)

```powershell
# Uses default Excel path: ../dataset generation/output/excel/universe_questions_models.xlsx
python batch_processor.py create --model "gpt-4o"

# Custom Excel path
python batch_processor.py create --excel-path "path/to/excel/file.xlsx" --model "gpt-4o"
```

For reasoning models (o3mini):

```powershell
python batch_processor.py create --model "o3-mini" --reasoning-effort "high"
```

### 2. Upload batches to OpenAI

```powershell
# Uses default request dir: output/batch_requests
python batch_processor.py upload --model "gpt-4o"

# With custom API key
python batch_processor.py upload --api-key "your-api-key" --model "gpt-4o"
```

### 3. Check batch status and download completed results (one-time check)

```powershell
# Uses default response dir: output/batch_responses
python batch_processor.py monitor
```

### 4. Find missing responses and create retry files

```powershell
# Uses model name from --model if --model-name not specified
python batch_processor.py missing --model "gpt-4o"

# With specific model name
python batch_processor.py missing --model-name "gpt-4o"
```

## Default Paths

- Excel input: `../dataset generation/output/excel/universe_questions_models.xlsx`
- Request files: `output/batch_requests/`
- Response files: `output/batch_responses/`

All paths can be overridden with command line arguments.

## Files

- `batch_processor.py` - Main script with complete workflow
- `utils.py` - Utility functions

## Requirements

```
openai
pandas
openpyxl
```
