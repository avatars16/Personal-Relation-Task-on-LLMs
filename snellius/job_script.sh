#!/bin/bash
#SBATCH --job-name=llm_processing
#SBATCH --output=sbatch_outputs/%x_%j_output.log
#SBATCH --error=sbatch_outputs/%x_%j_error.log
#SBATCH --time=4:00:00
#SBATCH --partition=gpu_h100
#SBATCH --gpus-per-node=1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem-per-gpu=64G
#SBATCH --cpus-per-task=8
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=b.evelo@students.uu.nl

# Load any required modules
module load 2024
module load cuDNN/9.5.0.50-CUDA-12.6.0
module load Python/3.12.3-GCCcore-13.3.0
module load CUDA/12.6.0

# Activate virtual environment
source /home/bevelo/prt/bin/activate

# Set environment variables
export HF_HOME=/scratch-shared/bevelo/huggingface
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Change to script directory
cd "$SLURM_SUBMIT_DIR"

# Run the processing with configurable parameters
python run_processing.py \
    --input-file "./universe_questions_models.xlsx" \
    --output-dir "./results" \
    --log-dir "./logs" \
    --models "meta-llama/Llama-3.3-70B-Instruct" \
    --batch-size 50 \
    --hf-token "HF TOKEN" \
    --save-frequency 20 \
    --gpu-monitor-interval 5.0 \
    --max-length 1000 \
    --temperature 0.7

echo "Job completed at $(date)"

