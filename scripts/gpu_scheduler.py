#!/usr/bin/env python3
"""GPU scheduler for managing GPU resources in multi-user environments.

This script monitors GPU availability, locks GPUs for exclusive use,
and runs training scripts when GPUs become available.

Usage:
    python scripts/run_with_gpu.py train.py --arg1 value --arg2 value
    python scripts/run_with_gpu.py --list-gpus          # List GPU status
    python scripts/run_with_gpu.py --wait-time 3600     # Max wait time
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# GPU lock file location
LOCK_DIR = Path.home() / ".unix_workflow" / "gpu_locks"
LOCK_TIMEOUT_MINUTES = 30  # Auto-release lock after this long


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


def get_lock_file(gpu_index: int) -> Path:
    """Get the lock file path for a GPU."""
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    return LOCK_DIR / f"gpu_{gpu_index}.lock"


def acquire_gpu_lock(gpu_index: int, job_id: str) -> bool:
    """Try to acquire a lock on a GPU.

    Args:
        gpu_index: GPU index to lock.
        job_id: Unique job identifier.

    Returns:
        True if lock acquired, False otherwise.
    """
    lock_file = get_lock_file(gpu_index)

    # Check if lock exists and is stale
    if lock_file.exists():
        try:
            with open(lock_file, "r") as f:
                lock_data = json.load(f)
            lock_time = datetime.fromisoformat(lock_data["timestamp"])
            age = datetime.now() - lock_time

            # If lock is older than timeout, it's stale
            if age.total_seconds() > LOCK_TIMEOUT_MINUTES * 60:
                logger.info(f"GPU {gpu_index} lock is stale ({age}), releasing...")
                lock_file.unlink()
            else:
                logger.debug(f"GPU {gpu_index} is locked by {lock_data.get('job_id', 'unknown')}")
                return False
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Invalid lock file for GPU {gpu_index}: {e}")
            lock_file.unlink()

    # Try to acquire lock
    try:
        lock_data = {
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "pid": os.getpid(),
        }
        # Use exclusive create to prevent race conditions
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, "w") as f:
            json.dump(lock_data, f, indent=2)
        logger.info(f"Acquired lock on GPU {gpu_index}")
        return True
    except FileExistsError:
        logger.debug(f"GPU {gpu_index} was locked by another process")
        return False


def release_gpu_lock(gpu_index: int) -> None:
    """Release a GPU lock.

    Args:
        gpu_index: GPU index to unlock.
    """
    lock_file = get_lock_file(gpu_index)
    if lock_file.exists():
        lock_file.unlink()
        logger.info(f"Released lock on GPU {gpu_index}")


def wait_for_gpu(
    required_gpus: int = 1,
    min_free_memory_mb: int = 8000,
    max_utilization_percent: int = 10,
    max_wait_time: int = 3600,
    check_interval: int = 30,
    job_id: str = None,
) -> Optional[List[int]]:
    """Wait for GPUs to become available.

    Args:
        required_gpus: Number of GPUs needed.
        min_free_memory_mb: Minimum free memory per GPU.
        max_utilization_percent: Maximum utilization per GPU.
        max_wait_time: Maximum time to wait in seconds.
        check_interval: How often to check in seconds.
        job_id: Unique job identifier for locking.

    Returns:
        List of GPU indices if available, None if timeout.
    """
    if job_id is None:
        job_id = f"job_{os.getpid()}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=max_wait_time)

    logger.info(f"Waiting for {required_gpus} GPU(s)...")
    logger.info(f"Requirements: {min_free_memory_mb}MB free, <{max_utilization_percent}% util")
    logger.info(f"Max wait time: {max_wait_time}s (until {end_time.strftime('%H:%M:%S')})")

    while datetime.now() < end_time:
        available = get_available_gpus(min_free_memory_mb, max_utilization_percent)

        if len(available) >= required_gpus:
            # Try to acquire locks
            selected = available[:required_gpus]
            locked = []

            for gpu_idx in selected:
                if acquire_gpu_lock(gpu_idx, job_id):
                    locked.append(gpu_idx)
                else:
                    # Failed to lock, release any we got
                    for idx in locked:
                        release_gpu_lock(idx)
                    break

            if len(locked) == required_gpus:
                logger.info(f"Acquired {required_gpus} GPU(s): {locked}")
                return locked

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
        lock_file = get_lock_file(gpu["index"])
        locked = "🔒" if lock_file.exists() else "  "
        print(f"{gpu['index']:<4} | {gpu['name']:<25} | {gpu['memory_free_mb']:>8}MB | {gpu['memory_used_mb']:>8}MB | {gpu['utilization_percent']:>5}% {locked}")

    print("=" * 70)

    # Show locked GPUs
    if LOCK_DIR.exists():
        locks = list(LOCK_DIR.glob("gpu_*.lock"))
        if locks:
            print("\nLocked GPUs:")
            for lock_file in locks:
                try:
                    with open(lock_file, "r") as f:
                        data = json.load(f)
                    gpu_idx = lock_file.stem.replace("gpu_", "")
                    age = datetime.now() - datetime.fromisoformat(data["timestamp"])
                    print(f"  GPU {gpu_idx}: {data.get('job_id', 'unknown')} ({int(age.total_seconds())}s ago)")
                except Exception:
                    pass


def clean_stale_locks() -> int:
    """Clean up stale lock files.

    Returns:
        Number of locks cleaned.
    """
    if not LOCK_DIR.exists():
        return 0

    cleaned = 0
    for lock_file in LOCK_DIR.glob("gpu_*.lock"):
        try:
            with open(lock_file, "r") as f:
                data = json.load(f)
            lock_time = datetime.fromisoformat(data["timestamp"])
            age = datetime.now() - lock_time

            if age.total_seconds() > LOCK_TIMEOUT_MINUTES * 60:
                lock_file.unlink()
                logger.info(f"Cleaned stale lock: {lock_file}")
                cleaned += 1
        except Exception:
            pass

    return cleaned


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run scripts with GPU scheduling and resource management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s train.py --lr 0.001 --epochs 100
  %(prog)s --list-gpus
  %(prog)s --wait-time 7200 train.py
  %(prog)s --gpus 2 --min-memory 16000 train.py
  %(prog)s --clean-locks
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
    parser.add_argument(
        "--check-interval",
        type=int,
        default=30,
        help="GPU check interval in seconds (default: 30)",
    )

    # Utility commands
    parser.add_argument(
        "--list-gpus",
        action="store_true",
        help="List GPU status and exit",
    )
    parser.add_argument(
        "--clean-locks",
        action="store_true",
        help="Clean up stale lock files and exit",
    )
    parser.add_argument(
        "--python",
        type=str,
        default=None,
        help="Python executable path (default: sys.executable)",
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

    if args.clean_locks:
        cleaned = clean_stale_locks()
        print(f"Cleaned {cleaned} stale lock(s)")
        return 0

    # Must provide a script
    if not args.script:
        parser = argparse.ArgumentParser()
        parser.print_help()
        print("\nError: Must provide a script to run or use --list-gpus / --clean-locks")
        return 1

    # Wait for GPU
    gpu_indices = wait_for_gpu(
        required_gpus=args.gpus,
        min_free_memory_mb=args.min_memory,
        max_utilization_percent=args.max_util,
        max_wait_time=args.wait_time,
        check_interval=args.check_interval,
    )

    if gpu_indices is None:
        logger.error("No GPUs available after waiting")
        return 1

    # Run the script
    exit_code = run_script_with_gpu(
        script=args.script,
        script_args=args.script_args,
        gpu_indices=gpu_indices,
        python_executable=args.python,
    )

    # Release GPU locks
    for idx in gpu_indices:
        release_gpu_lock(idx)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
