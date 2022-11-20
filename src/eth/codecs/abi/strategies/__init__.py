import hypothesis.strategies as st

from eth.codecs.abi.strategies.nodes import Node as st_node

schema = st.builds(str, st_node)
