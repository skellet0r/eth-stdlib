import hypothesis.strategies as st

from eth.codecs.abi import nodes

# limit max size of tuples and arrays, needs to be a reasonable number otherwise
# value generation will bork for exceedingly large numbers
MAXSIZE = 10
# limit the depth of recursive array and tuple strategies
MAXDEPTH = 3


# helper strategies
bits = st.sampled_from(range(8, 264, 8))

# atomic types
Address = st.builds(nodes.AddressNode)
Bool = st.builds(nodes.BooleanNode)
DynamicBytes = st.builds(nodes.BytesNode)
FixedBytes = st.builds(nodes.BytesNode, st.integers(1, 32))
Fixed = st.builds(nodes.FixedNode, bits, st.integers(0, 80), st.booleans())
Integer = st.builds(nodes.IntegerNode, bits, st.booleans())
String = st.builds(nodes.StringNode)

# all atomic types
Atomic = st.one_of(Address, Bool, DynamicBytes, FixedBytes, Fixed, Integer, String)

# static types, occupy 32 bytes
Static = Address | Bool | FixedBytes | Fixed | Integer
# dynamic types, occupy 32 bytes at minimum
Dynamic = DynamicBytes | String

# variations of array types
SS_Array = st.builds(nodes.ArrayNode, Static, st.integers(1, MAXSIZE))
DS_Array = st.builds(nodes.ArrayNode, Static, st.none())

SD_Array = st.builds(nodes.ArrayNode, Dynamic, st.integers(1, MAXSIZE))
DD_Array = st.builds(nodes.ArrayNode, Dynamic, st.none())

# variation of tuple types
S_Tuple = st.builds(
    nodes.TupleNode, st.builds(tuple, st.lists(Static, min_size=1, max_size=MAXSIZE))
)
D_Tuple = st.builds(
    nodes.TupleNode, st.builds(tuple, st.lists(Dynamic, min_size=1, max_size=MAXSIZE))
)


@st.deferred
def Array() -> st.SearchStrategy:
    size = st.none() | st.integers(1, MAXSIZE)
    array = st.builds(nodes.ArrayNode, Atomic | Tuple, size)
    # top-level will always be an array
    return st.recursive(array, lambda s: st.builds(nodes.ArrayNode, s, size), max_leaves=MAXDEPTH)


@st.deferred
def Tuple() -> st.SearchStrategy:
    components = st.builds(tuple, st.lists(Atomic | Array, min_size=1, max_size=MAXSIZE))
    tuple_ = st.builds(nodes.TupleNode, components)
    # top-level will always be a tuple
    return st.recursive(
        tuple_,
        lambda s: st.builds(
            nodes.TupleNode, st.builds(tuple, st.lists(s, min_size=1, max_size=MAXSIZE))
        ),
        max_leaves=MAXDEPTH,
    )


# recursive strategy for composite types - top-level can be any valid abi type
def extend(base: st.SearchStrategy) -> st.SearchStrategy:
    arrays = st.builds(nodes.ArrayNode, base, st.none() | st.integers(1, MAXSIZE))
    tuples = st.builds(
        nodes.TupleNode, st.builds(tuple, st.lists(base, min_size=1, max_size=MAXSIZE))
    )
    return arrays | tuples


Node = st.recursive(Atomic, extend, max_leaves=MAXDEPTH)
