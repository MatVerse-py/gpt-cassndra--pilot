from __future__ import annotations

import json
import sys
from datetime import datetime, UTC


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else "sem mensagem"
    print(
        json.dumps(
            {
                "message": message,
                "processed_at": datetime.now(UTC).isoformat(),
                "status": "processed",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
