"""Build the reported full-corpus knowledge-base index.

Set ``DOC_AGENT_RUN_MODE=small`` explicitly for a development-only run. A CPU
runner is supported even though the measured A2 evidence used Kaggle CUDA.
"""

import os

from doc_agent import config, pipeline

os.environ.setdefault("DOC_AGENT_RUN_MODE", "full")

cfg = config.load()
device_override = os.getenv("DOC_AGENT_DEVICE")
if device_override:
    cfg["device"] = device_override
elif str(cfg.get("device", "cpu")).lower().startswith("cuda"):
    import torch

    if not torch.cuda.is_available():
        cfg["device"] = "cpu"

pipeline.build_knowledge_base(cfg)
