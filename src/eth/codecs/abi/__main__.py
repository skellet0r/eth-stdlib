import argparse


def main():
    parser = argparse.ArgumentParser(
        "python -m eth.codecs.abi",
        description="A simple command line interface for the 'eth.codecs.abi' package.",
    )
    subparsers = parser.add_subparsers()

    parser_decode = subparsers.add_parser("decode", description="Decode a value.")
    parser_encode = subparsers.add_parser("encode", description="Encode a value.")

    for subparser in (parser_decode, parser_encode):
        subparser.add_argument("schema", help="An ABIv2 type schema.")
        subparser.add_argument(
            "value",
            nargs=argparse.REMAINDER,
            help=f"The value to {subparser.prog.split()[-1]}.",
        )

    print(parser.parse_args())


if __name__ == "__main__":
    main()
