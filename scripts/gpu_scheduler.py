#!/usr/bin/env python3
"""GPU scheduler for monitoring GPU availability and running training scripts.

This script monitors GPU availability using nvidia-smi and runs training
scripts when GPUs become available.

Usage:
    python scripts/gpu_scheduler.py train.py --arg1 value --arg2 value
    python scripts/gpu_scheduler.py --list-gpus          # List GPU status
    python scripts/gpu_scheduler.py --wait-time 3600     # Max wait time
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [GPU] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


def get_gpu_info() -> List[Dict]:
    """Get GPU information using nvidia-smi.

    Returns:
        List of GPU info dictionaries.
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        gpus = []
        for line in result.stdout.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                gpus.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "memory_total_mb": int(parts[2]),
                    "memory_used_mb": int(parts[3]),
                    "memory_free_mb": int(parts[4]),
                    "utilization_percent": int(parts[5]),
                })
        return gpus
    except FileNotFoundError:
        logger.warning("nvidia-smi not found - NVIDIA driver may not be installed")
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get GPU info: {e}")
        return []


def get_available_gpus(
    min_free_memory_mb: int = 8000,
    max_utilization_percent: int = 10,
) -> List[int]:
    """Get list of available GPU indices.

    Args:
        min_free_memory_mb: Minimum free memory required.
        max_utilization_percent: Maximum utilization allowed.

    Returns:
        List of available GPU indices.
    """
    gpus = get_gpu_info()
    available = []

    for gpu in gpus:
        if (gpu["memory_free_mb"] >= min_free_memory_mb and
                gpu["utilization_percent"] <= max_utilization_percent):
            available.append(gpu["index"])

    return available


def wait_for_gpu(
    required_gpus: int = 1,
    min_free_memory_mb: int = 8000,
    max_utilization_percent: int = 10,
    max_wait_time: int = 3600,
    check_interval: int = 30,
) -> Optional[List[int]]:
    """Wait for GPUs to become available.

    Args:
        required_gpus: Number of GPUs needed.
        min_free_memory_mb: Minimum free memory per GPU.
        max_utilization_percent: Maximum utilization per GPU.
        max_wait_time: Maximum time to wait in seconds.
        check_interval: How often to check in seconds.

    Returns:
        List of GPU indices if available, None if timeout.
    """
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=max_wait_time)

    logger.info(f"Waiting for {required_gpus} GPU(s)...")
    logger.info(f"Requirements: {min_free_memory_mb}MB free, <{max_utilization_percent}% util")
    logger.info(f"Max wait time: {max_wait_time}s (until {end_time.strftime('%H:%M:%S')})")

    while datetime.now() < end_time:
        available = get_available_gpus(min_free_memory_mb, max_utilization_percent)

        if len(available) >= required_gpus:
            selected = available[:required_gpus]
            logger.info(f"Found {required_gpus} available GPU(s): {selected}")
            return selected

        # Show status
        elapsed = (datetime.now() - start_time).seconds
        gpus_info = get_gpu_info()
        if gpus_info:
            status = ", ".join([
                f"GPU{g['index']}: {g['memory_free_mb']}MB free, {g['utilization_percent']}%"
                for g in gpus_info
            ])
            logger.debug(f"Waiting... ({elapsed}s) [{status}]")

        time.sleep(check_interval)

    logger.error(f"Timeout waiting for GPU after {max_wait_time}s")
    return None


def run_script_with_gpu(
    script: str,
    script_args: List[str],
    gpu_indices: List[int],
    python_executable: str = None,
) -> int:
    """Run a script with specified GPUs.

    Args:
        script: Script path to run.
        script_args: Arguments to pass to the script.
        gpu_indices: GPU indices to use.
        python_executable: Python executable path.

    Returns:
        Exit code of the script.
    """
    if python_executable is None:
        python_executable = sys.executable

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, gpu_indices))

    cmd = [python_executable, script] + script_args

    logger.info(f"Running: {' '.join(cmd)}")
    logger.info(f"Using GPUs: {gpu_indices} (CUDA_VISIBLE_DEVICES={env['CUDA_VISIBLE_DEVICES']})")

    try:
        result = subprocess.run(cmd, env=env, check=False)
        return result.returncode
    except Exception as e:
        logger.error(f"Failed to run script: {e}")
        return 1


def list_gpu_status() -> None:
    """Print current GPU status."""
    gpus = get_gpu_info()

    if not gpus:
        print("No GPUs found or nvidia-smi not available.")
        return

    print("\n" + "=" * 70)
    print("GPU Status")
    print("=" * 70)
    print(f"{'GPU':<4} | {'Name':<25} | {'Free':<10} | {'Used':<10} | {'Util':<6}")
    print("-" * 70)

    for gpu in gpus:
        print(f"{gpu['index']:<4} | {gpu['name']:<25} | {gpu['memory_free_mb']:>8}MB | {gpu['memory_used_mb']:>8}MB | {gpu['utilization_percent']:>5}%")

    print("=" * 70)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run scripts with GPU scheduling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s train.py --lr 0.001 --epochs 100
  %(prog)s --list-gpus
  %(prog)s --wait-time 7200 train.py
  %(prog)s --gpus 2 --min-memory 16000 train.py
        """,
    )

    # GPU scheduling options
    parser.add_argument(
        "--gpus", "-g",
        type=int,
        default=1,
        help="Number of GPUs required (default: 1)",
    )
    parser.add_argument(
        "--min-memory", "-m",
        type=int,
        default=8000,
        help="Minimum free GPU memory in MB (default: 8000)",
    )
    parser.add_argument(
        "--max-util",
        type=int,
        default=10,
        help="Maximum GPU utilization percent (default: 10)",
    )
    parser.add_argument(
        "--wait-time", "-w",
        type=int,
        default=3600,
        help="Maximum wait time in seconds (default: 3600)",
    )

    # Utility commands
    parser.add_argument(
        "--list-gpus",
        action="store_true",
        help="List GPU status and exit",
    )

    # Script to run (remaining arguments)
    parser.add_argument(
        "script",
        nargs="?",
        help="Script to run",
    )
    parser.add_argument(
        "script_args",
        nargs="*",
        help="Arguments for the script",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    setup_logging()
    args = parse_args()

    # Utility commands
    if args.list_gpus:
        list_gpu_status()
        return 0

    # Must provide a script
    if not args.script:
        parser = argparse.ArgumentParser()
        parser.print_help()
        print("\nError: Must provide a script to run or use --list-gpus")
        return 1

    # Wait for GPU
    gpu_indices = wait_for_gpu(
        required_gpus=args.gpus,
        min_free_memory_mb=args.min_memory,
        max_utilization_percent=args.max_util,
        max_wait_time=args.wait_time,
    )

    if gpu_indices is None:
        logger.error("No GPUs available after waiting")
        return 1

    # Run the script
    exit_code = run_script_with_gpu(
        script=args.script,
        script_args=args.script_args,
        gpu_indices=gpu_indices,
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
