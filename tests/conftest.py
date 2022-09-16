import os

from hypothesis import settings

# register profile for local development
settings.register_profile("dev", max_examples=25)

# use the default profile if an env var is not set
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))
