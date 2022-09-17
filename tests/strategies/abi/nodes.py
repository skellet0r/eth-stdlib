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
Address = st.just(nodes.Address())
Bool = st.just(nodes.Bool())
Bytes = st.builds(nodes.Bytes, st.just(-1) | st.integers(1, 32))
Fixed = st.builds(nodes.Fixed, bits, st.integers(0, 80), st.booleans())
Integer = st.builds(nodes.Integer, bits, st.booleans())
String = st.just(nodes.String())

# all atomic types
Atomic = st.one_of(Address, Bool, Bytes, Fixed, Integer, String)

# static types, occupy 32 bytes
Static = Address | Bool | st.builds(nodes.Bytes, st.integers(1, 32)) | Fixed | Integer
# dynamic types, occupy 32 bytes at minimum
Dynamic = st.just(nodes.Bytes(-1)) | String

# variations of array types
SS_Array = st.builds(nodes.Array, Static, st.integers(1, 10))
DS_Array = st.builds(nodes.Array, Static, st.just(-1))

SD_Array = st.builds(nodes.Array, Dynamic, st.integers(1, 10))
DD_Array = st.builds(nodes.Array, Dynamic, st.just(-1))

# variation of tuple types
S_Tuple = st.builds(nodes.Tuple, st.builds(tuple, st.lists(Static, min_size=1, max_size=10)))
D_Tuple = st.builds(nodes.Tuple, st.builds(tuple, st.lists(Dynamic, min_size=1, max_size=10)))


@st.deferred
def Array():
    size = st.just(-1) | st.integers(1, MAXSIZE)
    array = st.builds(nodes.Array, Atomic | Tuple, size)
    # top-level will always be an array
    return st.recursive(array, lambda s: st.builds(nodes.Array, s, size), max_leaves=MAXDEPTH)


@st.deferred
def Tuple():
    components = st.builds(tuple, st.lists(Atomic | Array, min_size=1, max_size=MAXSIZE))
    tuple_ = st.builds(nodes.Tuple, components)
    # top-level will always be a tuple
    return st.recursive(
        tuple_,
        lambda s: st.builds(
            nodes.Tuple, st.builds(tuple, st.lists(s, min_size=1, max_size=MAXSIZE))
        ),
        max_leaves=MAXDEPTH,
    )


# recursive strategy for composite types - top-level can be any valid abi type
def extend(base: st.SearchStrategy) -> st.SearchStrategy:
    arrays = st.builds(nodes.Array, base, st.just(-1) | st.integers(1, MAXSIZE))
    tuples = st.builds(nodes.Tuple, st.builds(tuple, st.lists(base, min_size=1, max_size=MAXSIZE)))
    return arrays | tuples


Node = st.recursive(Atomic, extend, max_leaves=MAXDEPTH)
