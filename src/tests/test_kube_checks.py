
from nose.tools import raises
from unittest import TestCase

from compose_flow.kube.checks import BaseChecker


class TestCheckerNoPrefix(BaseChecker):
    pass


class TestCheckerSingleCheck(BaseChecker):
    check_prefix = '_test_check_'

    def _test_check_noop(self, rendered: str) -> None:
        pass


class TestCheckerAlwaysError(BaseChecker):
    check_prefix = '_test_check_'

    def _test_check_always_return(self, rendered: str) -> str:
        return 'Fail!'


class TestBaseChecker(TestCase):
    @raises(AttributeError)
    def test_no_checks(self):
        """Ensure checker without a check_prefix errors out"""
        checker = TestCheckerNoPrefix()
        checker.check('')

    def test_noop_check(self):
        """Ensure checker with a single dummy checker runs"""
        checker = TestCheckerSingleCheck()
        errors = checker.check('')

        assert len(errors) == 0

    def test_always_error_check(self):
        checker = TestCheckerAlwaysError()
        errors = checker.check('')

        assert len(errors) > 0
        assert 'Fail!' in errors
