import argparse
import decimal
import json
from typing import Any, Callable, Optional, Sequence, Union

from eth.codecs.abi import nodes
from eth.codecs.abi.decoder import Decoder
from eth.codecs.abi.encoder import Encoder
from eth.codecs.abi.exceptions import CodecError, ParseError
from eth.codecs.abi.parser import Parser


class CLIEncoder(Encoder):
    @classmethod
    def visit_BytesNode(cls, node: nodes.BytesNode, value: str) -> bytes:
        value = value[2:] if value[:2].lower() == "0x" else value
        return super().visit_BytesNode(node, bytes.fromhex(value))

    @classmethod
    def visit_FixedNode(cls, node: nodes.FixedNode, value: Union[decimal.Decimal, int]) -> bytes:
        return super().visit_FixedNode(node, decimal.Decimal(value))


class CLIJSONDecoder(json.JSONDecoder):
    def decode(self, s: str, _w: Optional[Callable[..., Any]] = None) -> Any:
        return s if s.lower()[:2] == "0x" else super().decode(s)


class CLIJSONEncoder(json.JSONEncoder):
    def encode(self, o: Any) -> str:
        if isinstance(o, bytes):
            return "0x" + o.hex()
        return super().encode(o)


def decode(schema: str, value: Sequence[str]):
    parsed_schema = Parser.parse(schema)
    hexval = "" if not value else value[0]
    parsed_value = bytes.fromhex(hexval[2:] if hexval[:2].lower() == "0x" else hexval)
    print(json.dumps(Decoder.decode(parsed_schema, parsed_value), cls=CLIJSONEncoder))


def encode(schema: str, value: Sequence[str]):
    parsed_schema = Parser.parse(schema)
    parsed_value = json.loads(" ".join(value), parse_float=decimal.Decimal, cls=CLIJSONDecoder)
    print("0x" + CLIEncoder.encode(parsed_schema, parsed_value).hex())


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
    try:
        args.pop("func", parser.print_help)(**args)
    except json.JSONDecodeError:
        parser.exit(1, f"{' '.join(args['value'])!r} is not valid JSON.\n")
    except (CodecError, ParseError) as err:
        parser.exit(1, f"{err!s}\n")


if __name__ == "__main__":
    main()
