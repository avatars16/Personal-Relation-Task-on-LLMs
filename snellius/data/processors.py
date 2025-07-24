"""
Data processing modules for handling input data and results
This module contains the logic specific to processing Excel files with questions
"""
import pandas as pd
import os
import time
from tqdm import tqdm
import traceback
import logging
from typing import Dict, List, Any, Set, Optional, Tuple
from abc import ABC, abstractmethod

# Set up logging
logger = logging.getLogger(__name__)


class DataProcessor(ABC):
    """Abstract base class for data processors"""
    
    @abstractmethod
    def load_data(self, file_path: str) -> Any:
        """Load data from file"""
        pass
    
    @abstractmethod
    def process_data(self, data: Any, llm_engine: Any, config: Any) -> List[Dict[str, Any]]:
        """Process data using LLM engine"""
        pass
    
    @abstractmethod
    def save_results(self, results: List[Dict[str, Any]], output_path: str, output_format: str = "both") -> None:
        """Save results to file"""
        pass


class ExcelQuestionProcessor(DataProcessor):
    """Processor for Excel files containing questions and prompts"""
    
    def __init__(self):
        self.processed_questions: Set[str] = set()
    
    def extract_representation_approach(self, sheet_name: str) -> Tuple[str, str]:
        """Extract representation and approach from sheet name"""
        parts = sheet_name.strip().lower().split(',')
        
        representation = "unknown"
        approach = "unknown"
        
        if len(parts) >= 2:
            # Representation can be english or abstract
            if "english" in parts[0]:
                representation = "english"
            elif "abstract" in parts[0]:
                representation = "abstract"
            
            # Approach can be extensional or intensional
            if "extensional" in parts[1]:
                approach = "extensional"
            elif "intensional" in parts[1]:
                approach = "intensional"
        
        return representation, approach

    def is_sheet_fully_processed(self, df: pd.DataFrame, processed_questions: Set[str]) -> bool:
        """Check if all questions in a sheet have already been processed"""
        if 'QuestionId' not in df.columns:
            return False
        
        total_questions = len(df)
        processed_count = sum(1 for qid in df['QuestionId'] if qid in processed_questions)
        
        return processed_count == total_questions

    def validate_dataframe(self, df: pd.DataFrame, sheet_name: str) -> bool:
        """Validate that the dataframe has all required columns"""
        required_columns = ["Complexity", "Branching", "QuestionId", "Prompt", "Question", "Answer"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"Missing columns {missing_columns} in sheet {sheet_name}")
            return False
        return True

    def load_processed_questions(self, output_base: str) -> Set[str]:
        """Load previously processed questions from existing results"""
        processed_questions = set()
        
        # Check CSV file first
        csv_file = f"{output_base}.csv"
        if os.path.exists(csv_file):
            logger.info(f"Found existing CSV results file: {csv_file}")
            try:
                # Read only the QuestionId column to save memory
                previous_results = pd.read_csv(csv_file, usecols=['QuestionId'])
                processed_questions.update(previous_results['QuestionId'])
                logger.info(f"Found {len(processed_questions)} previously processed questions")
            except Exception as e:
                logger.error(f"Error reading previous CSV results: {str(e)}")
        
        return processed_questions

    def load_data(self, file_path: str) -> pd.ExcelFile:
        """Load Excel file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        logger.info(f"Loading Excel file: {file_path}")
        return pd.ExcelFile(file_path)

    def process_result(self, row: pd.Series, model_result: Dict[str, Any], 
                      representation: str, approach: str, model: str) -> Dict[str, Any]:
        """Process a single model result and return a structured result dictionary"""
        model_answer = model_result["response"]
        duration = model_result["duration"]
        input_tokens = model_result["input_tokens"]
        output_tokens = model_result["output_tokens"]
        total_tokens = model_result["total_tokens"]
        
        result = {
            "Representation": representation,
            "Approach": approach,
            "Complexity": row["Complexity"],
            "Branching": row["Branching"],
            "QuestionId": row["QuestionId"],
            "Prompt": row["Prompt"],
            "Question": row["Question"],
            "Correct_Answer": row["Answer"],
            "Model_Answer": model_answer,
            "Duration": duration,
            "Input_Tokens": input_tokens,
            "Output_Tokens": output_tokens,
            "Total_Tokens": total_tokens,
            "Model": model,
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Mark as processed
        self.processed_questions.add(row["QuestionId"])
        
        return result

    def process_batch(self, batch_prompts: List[str], batch_rows: List[pd.Series], 
                     llm_engine: Any, representation: str, approach: str, model: str) -> List[Dict[str, Any]]:
        """Process a batch of prompts and return results"""
        results = []
        
        try:
            # Process as batch or individual based on batch size
            if len(batch_prompts) > 1:
                logger.info(f"Processing batch of {len(batch_prompts)} prompts")
                model_results = llm_engine.batch_generate(batch_prompts)
            else:
                # Single prompt processing
                result = llm_engine.generate_response(batch_prompts[0])
                model_results = [result]
            
            # Process each result
            for row, model_result in zip(batch_rows, model_results):
                result_dict = self.process_result(row, model_result, representation, approach, model)
                results.append(result_dict)
                logger.info(f"Processed question {row['QuestionId']}")
                
            return results
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            traceback.print_exc()
            return results  # Return any results we were able to process

    def save_results(self, results: List[Dict[str, Any]], output_path_without_extension: str, 
                    output_format: str = "both") -> None:
        """Save results to CSV and/or Excel files"""
        if not results:
            logger.warning("No results to save")
            return
            
        if output_format in ["csv", "both"]:
            results_csv = results.copy()
            for r in results_csv:
                if isinstance(r.get("Prompt"), str):
                    r["Prompt"] = r["Prompt"].replace("\n", "\\n")
                if isinstance(r.get("Model_Answer"), str):
                    r["Model_Answer"] = r["Model_Answer"].replace("\n", "\\n")
            
            df_csv = pd.DataFrame(results_csv)
            csv_path = f"{output_path_without_extension}.csv"
            
            if os.path.exists(csv_path):
                df_csv.to_csv(csv_path, mode='a', header=False, index=False)
            else:
                df_csv.to_csv(csv_path, index=False)
        
        if output_format in ["excel", "both"]:
            df = pd.DataFrame(results)
            excel_path = f"{output_path_without_extension}.xlsx"
            
            if os.path.exists(excel_path):
                try:
                    with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
                        df.to_excel(writer, index=False, sheet_name='Results')
                except Exception as e:
                    logger.error(f"Error appending to Excel: {e}. Creating new file.")
                    df.to_excel(excel_path, index=False)
            else:
                df.to_excel(excel_path, index=False)
        
        logger.info(f"Results saved ({len(results)} entries) to {output_format} format")

    def process_data(self, data: pd.ExcelFile, llm_engine: Any, config: Any) -> List[Dict[str, Any]]:
        """Process Excel data using LLM engine"""
        # Generate output filename base (without extension)
        model_name = config.models[0] if config.models else "unknown_model"
        output_base = os.path.join(
            config.output_dir, 
            model_name.replace(':', '_').replace('/', '-').replace('\\', '-') + "_results"
        )
        
        # Load previously processed questions
        self.processed_questions = self.load_processed_questions(output_base)
        
        # Get sheet names
        sheet_names = data.sheet_names
        logger.info(f"Found {len(sheet_names)} sheets: {sheet_names}")
        
        all_results = []
        row_count = 0
        total_processed = 0
        batch_size = config.batch_size
        
        # Process each sheet
        for sheet_name in sheet_names:
            # Extract representation and approach from sheet name
            representation, approach = self.extract_representation_approach(sheet_name)
            logger.info(f"\nProcessing sheet: {sheet_name} (Representation: {representation}, Approach: {approach})")
            
            try:
                # Read sheet with only the required columns to save memory
                required_columns = ["Complexity", "Branching", "QuestionId", "Prompt", "Question", "Answer"]
                df = pd.read_excel(data, sheet_name=sheet_name, usecols=required_columns)
                logger.info(f"Sheet contains {len(df)} questions")
        
                # Check if required columns exist
                if not self.validate_dataframe(df, sheet_name):
                    logger.warning(f"Missing required columns in sheet {sheet_name}. Skipping.")
                    continue
                
                # Check if sheet is fully processed
                if self.is_sheet_fully_processed(df, self.processed_questions):
                    logger.info(f"Sheet {sheet_name} is already fully processed. Skipping.")
                    continue
                    
                # Initialize batch processing variables
                batch_prompts = []
                batch_rows = []
                
                # Process each row
                for row_idx, row in tqdm(df.iterrows(), total=len(df), desc=f"Processing {sheet_name}"):
                    # Use QuestionId directly from the Excel file
                    question_id = row['QuestionId']
                    if question_id in self.processed_questions:
                        logger.debug(f"Question already processed: {question_id}. Skipping.")
                        continue
                    
                    # Add to batch
                    batch_prompts.append(row['Prompt'])
                    batch_rows.append(row)
                    
                    # Process batch if it's full or this is the last row
                    is_last_row = row_idx == len(df) - 1
                    if len(batch_prompts) >= batch_size or is_last_row:
                        # Process the batch
                        batch_results = self.process_batch(
                            batch_prompts, batch_rows, llm_engine, 
                            representation, approach, model_name
                        )
                        
                        # Add batch results to all results
                        all_results.extend(batch_results)
                        row_count += len(batch_results)
                        total_processed += len(batch_results)
                        
                        # Reset batch data and increase batch size
                        batch_prompts = []
                        batch_rows = []
                        batch_size += 50
                        logger.info(f"Increasing batch size to {batch_size}")
                        
                        # Save at regular intervals
                        if row_count >= config.save_frequency:
                            self.save_results(all_results, output_base, config.output_format)
                            all_results = []  # Clear results after saving to free memory
                            row_count = 0
                    
            except Exception as e:
                logger.error(f"Error processing sheet {sheet_name}: {e}")
                traceback.print_exc()
                # Save what we have so far if there's an error
                if all_results:
                    self.save_results(all_results, output_base, config.output_format)
                    all_results = []
                    row_count = 0
        
        # Save any remaining results
        if all_results:
            self.save_results(all_results, output_base, config.output_format)
        
        logger.info(f"Processing complete for {model_name}. Total new questions processed: {total_processed}")
        return all_results
