import pandas as pd
import os
import re

# Script to remove personal identifiable information (PII) columns from PCIbex Farm results files.


def remove_columns_from_pcibex_file(file_path, columns_to_remove):
    """
    Remove specified columns from a PCIbex Farm results file and update all column comments.
    
    Args:
        file_path (str): Path to the CSV file
        columns_to_remove (list): List of column indices to remove (0-based)
    """
    print(f"Processing: {file_path}")
    
    # Read the file line by line
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Process each line
    processed_lines = []
    for line in lines:
        # Check if this is a comment line with column definitions
        if line.strip().startswith('#') and '. ' in line:
            # Handle specific column comments that need to be removed or renumbered
            if '# 13. SESSION_ID.' in line or '# 14. STUDY_ID.' in line or '# 15. PROLIFIC_PID.' in line:
                # Skip these lines (remove them)
                continue
            elif re.match(r'# (\d+)\. ', line.strip()):
                # This is a numbered column comment - check if we need to renumber
                match = re.match(r'# (\d+)\. (.+)', line.strip())
                if match:
                    col_num = int(match.group(1))
                    col_name = match.group(2)
                    
                    # If column number > 15, subtract 3 (for the 3 removed columns)
                    if col_num > 15:
                        new_col_num = col_num - 3
                        processed_lines.append(f"# {new_col_num}. {col_name}\n")
                    else:
                        processed_lines.append(line)
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        elif not line.strip().startswith('#') and line.strip():
            # This is a data line - remove the specified columns
            columns = line.strip().split(',')
            # Remove columns in reverse order to maintain indices
            for col_idx in sorted(columns_to_remove, reverse=True):
                if col_idx < len(columns):
                    columns.pop(col_idx)
            processed_lines.append(','.join(columns) + '\n')
        else:
            # Keep all other lines (empty lines, other comments)
            processed_lines.append(line)
    
    # Create backup of original file
    backup_path = file_path.replace('.csv', '_backup3.csv')
    print(f"Creating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # Write the processed file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)
    
    print(f"Columns removed and all comments updated successfully from: {file_path}")

def main():
    """
    Main function to process both experiment files.
    """
    # Define the base directory
    base_dir = r"c:\Users\Bart Evelo\OneDrive\Documenten\Universiteit\Linguistics\Thesis\Code final\thesis bart\results\humans"
    
    # Files to process
    files_to_process = [
        os.path.join(base_dir, "results_prod_exp1.csv"),
        os.path.join(base_dir, "results_prod_exp2.csv")
    ]
    
    # Column indices to remove (0-based indexing)
    # Based on PCIbex Farm format:
    # Column 13 (index 12): SESSION_ID
    # Column 14 (index 13): STUDY_ID  
    # Column 15 (index 14): PROLIFIC_PID
    columns_to_remove = [12, 13, 14]  # SESSION_ID, STUDY_ID, PROLIFIC_PID
    
    print("PCIbex Farm Results Column Remover (Updated)")
    print("=" * 45)
    print(f"Removing columns at indices: {columns_to_remove}")
    print("(SESSION_ID, STUDY_ID, PROLIFIC_PID)")
    print("This will also update ALL comment numbering throughout the files.")
    print()
    
    # Process each file
    for file_path in files_to_process:
        if os.path.exists(file_path):
            try:
                remove_columns_from_pcibex_file(file_path, columns_to_remove)
                print(f"✓ Successfully processed: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"✗ Error processing {os.path.basename(file_path)}: {str(e)}")
        else:
            print(f"✗ File not found: {file_path}")
        print()
    
    print("Processing complete!")
    print("\nNote: Original files have been backed up with '_backup3.csv' suffix.")

if __name__ == "__main__":
    main()