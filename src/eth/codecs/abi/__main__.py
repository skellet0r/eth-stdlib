import argparse
from typing import Sequence


def decode(schema: str, value: Sequence[str]):
    print(schema, value)


def encode(schema: str, value: Sequence[str]):
    print(schema, value)


def main():
    parser = argparse.ArgumentParser(
        "python -m eth.codecs.abi",
        description="A simple command line interface for the 'eth.codecs.abi' package.",
    )
    subparsers = parser.add_subparsers(title="Available commands")

    parser_decode = subparsers.add_parser("decode", description="Decode a value.")
    parser_decode.set_defaults(func=decode)

    parser_encode = subparsers.add_parser("encode", description="Encode a value.")
    parser_encode.set_defaults(func=encode)

    # common arguments
    for subparser in (parser_decode, parser_encode):
        subparser.add_argument("schema", help="An ABIv2 type schema.")
        subparser.add_argument(
            "value",
            nargs=argparse.REMAINDER,
            help=f"The value to {subparser.prog.split()[-1]}.",
        )

    args = vars(parser.parse_args())
    args.pop("func", parser.print_help)(**args)


if __name__ == "__main__":
    main()
