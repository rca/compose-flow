
from nose.tools import raises
from unittest import TestCase

from compose_flow.kube.checks import BaseChecker


class TestCheckerNoPrefix(BaseChecker):
    pass


class TestCheckerSingleCheck(BaseChecker):
    check_prefix = '_test_check_'

    def _test_check_noop(self):
        pass


class TestBaseChecker(TestCase):
    @raises(AttributeError)
    def test_get_no_checks(self):
        """Ensure checker without a check_prefix errors out"""
        checker = TestCheckerNoPrefix()
        checker.check('')
