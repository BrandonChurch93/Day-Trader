"""Plan 18 draft: the only mode tests made-up inputs."""
import argparse
import unittest

from . import test_18


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", required=True)
    parser.parse_args()
    tests = unittest.defaultTestLoader.loadTestsFromModule(test_18)
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if not result.wasSuccessful():
        return 1
    test_18.power()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
