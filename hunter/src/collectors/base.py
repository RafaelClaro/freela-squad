"""The collector contract.

Every source of opportunities (Freelancer, Upwork, manual input, future sites)
is a Collector. The Hunter core never knows which source it came from — it only
knows it receives a list of Opportunity objects. This is the white-label seam:
sources are pluggable, the qualification core is fixed.
"""

from abc import ABC, abstractmethod

from src.models import Opportunity


class Collector(ABC):
    """Base class every opportunity source must implement."""

    @abstractmethod
    def collect(self) -> list[Opportunity]:
        """Fetch opportunities from this source and return them as Opportunity objects.

        Each concrete collector is responsible for translating its source's raw
        data into the common Opportunity format. The core pipeline depends only
        on this contract, never on the source's specifics.
        """
        raise NotImplementedError
