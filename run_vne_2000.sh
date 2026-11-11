#!/bin/bash
#SBATCH --job-name=vne_experiments
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=2-00:00:00
#SBATCH --output=vne_%j.out
#SBATCH --error=vne_%j.err

set -e

cd "$HOME/vne-using-2-level-gaming-approach"

source vne-env/bin/activate
export PYTHONPATH="$HOME/alib-py3:$PYTHONPATH"
export PYTHONUNBUFFERED=1

echo "Starting VNE experiments: $(date)"
python main.py 2000
echo "Finished VNE experiments: $(date)"
