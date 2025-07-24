"""
Utilities for processing OpenAI batch requests and responses.
"""

import pandas as pd
import json
import os
from utils.file_utils import get_output_directory

def excel_to_jsonl(excel_path, output_dir, model="gpt-4o", reasoning_effort=None):
    """
    Convert each sheet in an Excel file to a separate JSONL file for OpenAI batch processing.
    
    Args:
        excel_path (str): Path to the Excel file
        output_dir (str): Directory to save the JSONL files
        model (str): The OpenAI model to use
        reasoning_effort (str): Reasoning effort level for reasoning models
        
    Returns:
        dict: Dictionary mapping sheet names to batch information
    """
    output_dir = get_output_directory(output_dir)
    
    excel_file = pd.ExcelFile(excel_path)
    sheet_names = excel_file.sheet_names
    
    print(f"Found {len(sheet_names)} sheets: {sheet_names}")
    
    batch_ids = {}
    
    for sheet_name in sheet_names:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        output_file = os.path.join(output_dir, f"{sheet_name.replace(',', '_')}.jsonl")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                question_id = row['QuestionId']
                prompt = row['Prompt']
                
                request = {
                    "custom_id": question_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                    }
                }
                
                if reasoning_effort is not None:
                    request["body"]["reasoning_effort"] = reasoning_effort
                
                f.write(json.dumps(request) + '\n')
        
        print(f"Created {output_file} with {len(df)} requests")
    
    return batch_ids


def create_batch_requests_from_excel():
    """Main function to create batch request files from Excel"""
    excel_path = os.path.join(get_output_directory('excel'), "universe_questions_models.xlsx")
    output_dir = "batch_requests"
    
    model = "o3-mini-2025-01-31"
    reasoning_effort = "high"  # For reasoning models like o3-mini, o1
    
    excel_to_jsonl(excel_path, output_dir, model, reasoning_effort)
    print("All sheets processed successfully!")


if __name__ == "__main__":
    create_batch_requests_from_excel()
