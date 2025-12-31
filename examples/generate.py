#!/usr/bin/env python3
"""Generate tasks example."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import GenerationConfig, OutputWriter
from src import ChessGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate reasoning tasks")
    parser.add_argument("--num-samples", type=int, default=10, help="Number of tasks")
    parser.add_argument("--output", type=str, default="data/questions", help="Output directory")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--domain", type=str, default="chess", help="Task domain")
    
    args = parser.parse_args()
    
    print(f"🎲 Generating {args.num_samples} {args.domain} tasks...")
    
    config = GenerationConfig(
        num_samples=args.num_samples,
        domain=args.domain,
        random_seed=args.seed,
        output_dir=Path(args.output)
    )
    
    generator = ChessGenerator(config)
    tasks = generator.generate_dataset()
    
    writer = OutputWriter(Path(args.output))
    writer.write_dataset(tasks)
    
    print(f"🎉 Done! Generated {len(tasks)} tasks in {args.output}/{args.domain}_task/")


if __name__ == "__main__":
    main()
