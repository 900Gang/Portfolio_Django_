"""
Test runner that clears the cache before every test.

The rate limits and the admin lockout keep their counters in the cache, which
Django's test runner does not reset between tests. Without this, requests
made by one test would count against the next and the suite would depend on
test order.
"""
import unittest

from django.core.cache import cache
from django.test.runner import DiscoverRunner


class CacheClearingRunner(DiscoverRunner):
    def get_resultclass(self):
        base = super().get_resultclass() or unittest.TextTestResult

        class CacheClearingResult(base):
            def startTest(self, test):
                cache.clear()
                super().startTest(test)

        return CacheClearingResult
