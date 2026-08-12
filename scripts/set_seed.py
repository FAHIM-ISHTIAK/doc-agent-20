"""Deterministic seeds for reproducible local and Kaggle runs."""

from __future__ import annotations

import json
import os
import random

import numpy as np
import torch

from doc_agent import config


def set_seed(seed: int) -> dict[str, bool | int]:
    """Seed Python, NumPy, CPU Torch, and every visible CUDA device."""

    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    cuda_available = torch.cuda.is_available()
    if cuda_available:
        torch.cuda.manual_seed_all(seed)

    torch.use_deterministic_algorithms(True, warn_only=True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True

    return {
        "seed": seed,
        "cuda_available": cuda_available,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
    }


def main() -> None:
    seed = int(config.load()["seed"])
    print(json.dumps(set_seed(seed), indent=2))


if __name__ == "__main__":
    main()
