from abc import ABC, abstractmethod

class MusicProvider(ABC):
    name: str
    @abstractmethod
    def generate(self, plan):
        """Return independently playable stems or raise a structured failure."""

class ExternalProvider(MusicProvider):
    """Integration contract only. No undocumented endpoint or provider is assumed."""
    name = "external_unconfigured"
    def generate(self, plan):
        raise RuntimeError("No external provider adapter is configured; no request was sent")

class MockProvider(MusicProvider):
    name = "mock_test_only"
    def generate(self, plan):
        raise RuntimeError("Mock provider is for tests only and is not enabled for production jobs")
