import os

from dotenv import load_dotenv
from hypothesis import settings

# modifies environment, loading env vars from '.env'
load_dotenv()

# register profile for local development
settings.register_profile("dev", max_examples=30)

# use the default profile if an env var is not set
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))
