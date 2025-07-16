import tyro
from dataclasses import dataclass


@dataclass
class Args:
    input_file: str
    verbose: bool = False
    num_threads: int = 4


def main():
    args = tyro.cli(Args)
    print(f"Input: {args.input_file}")
    print(f"Verbose: {args.verbose}")
    print(f"Threads: {args.num_threads}")


if __name__ == "__main__":
    main()
