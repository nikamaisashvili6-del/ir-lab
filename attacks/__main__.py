"""Runner: python -m attacks <scenario>. One line and exit 1 when a target is down."""

import importlib
import sys

from attacks.guard import OutOfLabError
from attacks.mgmt import TargetUnreachable
from attacks.registry import SCENARIOS


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in SCENARIOS:
        print(f"usage: python -m attacks <{'|'.join(SCENARIOS)}>", file=sys.stderr)
        return 2
    scenario = SCENARIOS[argv[0]]
    module = importlib.import_module(f"attacks.{scenario.module}")
    try:
        module.run()
    except TargetUnreachable as exc:
        print(f"Attack stopped: {exc}", file=sys.stderr)
        return 1
    except (OutOfLabError, RuntimeError) as exc:
        print(f"Attack failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
