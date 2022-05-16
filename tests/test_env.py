"""
Tests rss generation.
"""

import os
import unittest
from pprint import pprint


class EnvTester(unittest.TestCase):
    """Tests the functionality of the rss algorithm."""

    def tests_env_printout(self) -> None:  # pylint: disable=no-self-use
        """Simply prints out the environment variables."""
        pprint(dict(os.environ))


if __name__ == "__main__":
    unittest.main()
