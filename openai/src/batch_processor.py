"""
OpenAI Batch Processing Tool

This script handles the complete workflow for OpenAI batch processing:
1. Convert Excel files to JSONL batch requests
2. Upload batches to OpenAI
3. Monitor batch status and download results
4. Find missing responses and create retry batches
"""

import argparse
import os
import json
import time
import pandas as pd
from openai import OpenAI


class BatchProcessor:
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
    
    def excel_to_jsonl(self, excel_path, output_dir, model="gpt-4o", reasoning_effort=None):
        """Convert Excel sheets to JSONL batch request files"""
        os.makedirs(output_dir, exist_ok=True)
        
        excel_file = pd.ExcelFile(excel_path)
        print(f"Processing {len(excel_file.sheet_names)} sheets from {excel_path}")
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            output_file = os.path.join(output_dir, f"{sheet_name}.jsonl")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for _, row in df.iterrows():
                    request = {
                        "custom_id": row['QuestionId'],
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {
                            "model": model,
                            "messages": [{"role": "user", "content": row['Prompt']}]
                        }
                    }
                    
                    if reasoning_effort:
                        request["body"]["reasoning_effort"] = reasoning_effort
                    
                    f.write(json.dumps(request) + '\n')
            
            print(f"Created {output_file} with {len(df)} requests")
    
    def upload_batch(self, jsonl_path, description=None):
        """Upload a JSONL file as a batch to OpenAI"""
        with open(jsonl_path, 'rb') as f:
            batch_input_file = self.client.files.create(file=f, purpose="batch")
        
        batch = self.client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": description or os.path.basename(jsonl_path)}
        )
        
        print(f"Batch created: {batch.id} for {jsonl_path}")
        return batch.id
    
    def check_batch_status(self, batch_id):
        """Check the status of a batch"""
        batch = self.client.batches.retrieve(batch_id)
        return batch.status, batch
    
    def download_results(self, batch_id, output_path):
        """Download batch results to a file"""
        batch = self.client.batches.retrieve(batch_id)
        
        if batch.status != "completed":
            print(f"Batch {batch_id} is not completed yet. Status: {batch.status}")
            return False
        
        if batch.output_file_id:
            result = self.client.files.content(batch.output_file_id)
            with open(output_path, 'wb') as f:
                f.write(result.content)
            print(f"Results saved to {output_path}")
            return True
        
        return False
    
    def monitor_batches(self, batch_ids, output_dir, check_interval=60):
        """Monitor multiple batches and download results when complete"""
        os.makedirs(output_dir, exist_ok=True)
        completed = set()
        
        while len(completed) < len(batch_ids):
            for batch_id, filename in batch_ids.items():
                if batch_id in completed:
                    continue
                
                status, batch = self.check_batch_status(batch_id)
                print(f"Batch {batch_id} ({filename}): {status}")
                
                if status == "completed":
                    output_path = os.path.join(output_dir, filename)
                    if self.download_results(batch_id, output_path):
                        completed.add(batch_id)
                elif status == "failed":
                    print(f"Batch {batch_id} failed!")
                    completed.add(batch_id)
            
            if len(completed) < len(batch_ids):
                print(f"Waiting {check_interval} seconds before next check...")
                time.sleep(check_interval)
        
        print("All batches completed!")
    
    def find_missing_responses(self, request_dir, response_dir, model_name):
        """Find missing responses and create retry batch files"""
        file_types = ['english_extensional', 'english_intensional', 'abstract_extensional', 'abstract_intensional']
        
        for file_type in file_types:
            request_file = os.path.join(request_dir, f"{file_type}.jsonl")
            response_file = os.path.join(response_dir, f"{file_type}-{model_name}.jsonl")
            
            if not os.path.exists(request_file):
                print(f"Skipping {file_type}: request file not found")
                continue
            
            original_requests = self._load_jsonl_requests(request_file)
            response_ids = self._load_jsonl_ids(response_file)
            missing_ids = set(original_requests.keys()) - response_ids
            
            if missing_ids:
                print(f"{file_type}: Found {len(missing_ids)} missing responses")
                output_file = os.path.join(request_dir, f"{file_type}_{model_name}_missing.jsonl")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    for missing_id in sorted(missing_ids):
                        f.write(json.dumps(original_requests[missing_id]) + '\n')
                
                print(f"Created retry file: {output_file}")
            else:
                print(f"{file_type}: No missing responses")
    
    def _load_jsonl_requests(self, filepath):
        """Load JSONL requests as dict keyed by custom_id"""
        requests = {}
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line.strip())
                    requests[data['custom_id']] = data
        return requests
    
    def _load_jsonl_ids(self, filepath):
        """Load custom_ids from JSONL response file"""
        ids = set()
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        ids.add(data['custom_id'])
        return ids


def main():
    parser = argparse.ArgumentParser(description='OpenAI Batch Processing Tool')
    parser.add_argument('action', choices=['create', 'upload', 'monitor', 'missing'], 
                       help='Action to perform')
    parser.add_argument('--excel-path', help='Path to Excel file with prompts')
    parser.add_argument('--request-dir', default='batch_requests', help='Directory for batch request files')
    parser.add_argument('--response-dir', default='batch_responses', help='Directory for batch response files')
    parser.add_argument('--model', default='gpt-4o', help='OpenAI model to use')
    parser.add_argument('--reasoning-effort', choices=['low', 'medium', 'high'], 
                       help='Reasoning effort for reasoning models')
    parser.add_argument('--check-interval', type=int, default=60, 
                       help='Seconds between batch status checks')
    
    args = parser.parse_args()
    processor = BatchProcessor()
    
    if args.action == 'create':
        if not args.excel_path:
            print("Error: --excel-path required for create action")
            return
        processor.excel_to_jsonl(args.excel_path, args.request_dir, args.model, args.reasoning_effort)
    
    elif args.action == 'upload':
        batch_ids = {}
        for filename in os.listdir(args.request_dir):
            if filename.endswith('.jsonl') and not 'missing' in filename:
                jsonl_path = os.path.join(args.request_dir, filename)
                batch_id = processor.upload_batch(jsonl_path, f"{args.model}_{filename}")
                response_filename = f"{filename.replace('.jsonl', '')}-{args.model}.jsonl"
                batch_ids[batch_id] = response_filename
        
        print(f"\nCreated {len(batch_ids)} batches:")
        for batch_id, filename in batch_ids.items():
            print(f"  {batch_id}: {filename}")
    
    elif args.action == 'monitor':
        print("Enter batch IDs and filenames (format: batch_id:filename.jsonl)")
        print("Press Enter on empty line when done:")
        batch_ids = {}
        while True:
            line = input().strip()
            if not line:
                break
            try:
                batch_id, filename = line.split(':', 1)
                batch_ids[batch_id.strip()] = filename.strip()
            except ValueError:
                print("Invalid format. Use: batch_id:filename.jsonl")
        
        if batch_ids:
            processor.monitor_batches(batch_ids, args.response_dir, args.check_interval)
    
    elif args.action == 'missing':
        if not args.model_name:
            print("Error: --model-name required for missing action")
            return
        processor.find_missing_responses(args.request_dir, args.response_dir, args.model)


if __name__ == "__main__":
    main()
