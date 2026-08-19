"""Export the embedding model to ONNX and quantise it to INT8.

Produces the two optimised variants ``scripts/benchmark_onnx.py`` measures.
The export is checked against the PyTorch model it came from before it is
kept — at several sequence lengths, because ``torch.onnx.export`` traces one
concrete forward pass and transformers' attention path contains data-dependent
Python branches that could bake a constant into the graph.

The exported files are derived artifacts and are not tracked: ~130MB fp32 and
~34MB INT8 for a model whose weights are themselves untracked. What travels in
git is this script, the checks it runs, and the report the benchmark writes.

Usage:
    python scripts/export_onnx.py --profile finetuned
    python scripts/export_onnx.py --model BAAI/bge-small-en-v1.5
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duediligence.config import load_config  # noqa: E402
from duediligence.index.onnx_embed import export_onnx, onnx_export_dir  # noqa: E402

logger = logging.getLogger("export-onnx")

#: Written beside the weights rather than into ``results/``: it describes an
#: untracked artifact on this disk, and the benchmark folds it into the
#: tracked report so a reader sees the sizes and the parity numbers together
#: with what they cost in recall.
EXPORT_REPORT_FILENAME = "export.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default=None,
        help="model to export; defaults to the configured embedding model",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="config profile naming the model to export, e.g. 'finetuned'",
    )
    parser.add_argument("--out", default=None, help="export directory (default: models/onnx/<name>)")
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="export fp32 only, skipping INT8 quantisation",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    model_name = args.model or load_config(profile=args.profile).models.embedding_model
    out_dir = Path(args.out) if args.out else onnx_export_dir(model_name)

    report = export_onnx(model_name, out_dir=out_dir, quantize=not args.no_quantize)

    report_path = out_dir / EXPORT_REPORT_FILENAME
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    print(f"\nexported {model_name} -> {out_dir}")
    for name, variant in report["variants"].items():
        parity = variant["parity"]
        print(
            f"  {name:<10} {variant['bytes'] / 1e6:>7.1f} MB   "
            f"min cosine vs torch {parity['min_cosine_vs_torch']:.6f}"
        )
    print(f"\nwrote {report_path}")


if __name__ == "__main__":
    main()
