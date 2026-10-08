import json
import sys

from app.services.deploy import deploy


def main() -> int:
    result = deploy()
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
