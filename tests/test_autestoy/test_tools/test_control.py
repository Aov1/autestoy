from conftest import log

from autestoy.export.term import Term
from autestoy.tools.control import TrySeconds


def test_try_seconds():
    log("test_try_seconds")
    Term.sw_absolute_timestamp = True
    ts = TrySeconds(1.0)
    while ts:
        pass

    assert ts.check_timeout() is True
