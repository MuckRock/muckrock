# crowdsource/oembed_providers.py

# Third Party
from micawber import Provider, bootstrap_basic

# Create a registry with default providers (YouTube, Vimeo, Flickr, etc.)
PROVIDERS = bootstrap_basic()

# Add DocumentCloud support
PROVIDERS.register(
    r"https?://(www\.)?documentcloud\.org/.*",
    Provider("https://api.www.documentcloud.org/api/oembed/"),
)
