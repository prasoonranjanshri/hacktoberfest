"""Orchestrate end-to-end ML pipeline and write output artifacts."""

import argparse


def run(
    out_dir: str = "artifacts",
    seed: int = 42,
    n_accounts: int = 3000,
    days: int = 30,
) -> None:
    """Run full pipeline: simulate, extract features, train models, explain, validate, and write artifacts."""
    raise NotImplementedError("Implemented by Dev 1")


def main() -> None:
    """CLI entrypoint for running the ML pipeline."""
    parser = argparse.ArgumentParser(description="MuleNet ML pipeline runner")
    parser.add_argument("--out", default="artifacts", help="Output directory for artifacts")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--quick", action="store_true", help="Quick mode with 1000 accounts")
    parser.add_argument("--days", type=int, default=30, help="Simulation days")
    args = parser.parse_args()

    n_accounts = 1000 if args.quick else 3000
    run(out_dir=args.out, seed=args.seed, n_accounts=n_accounts, days=args.days)


if __name__ == "__main__":
    main()
