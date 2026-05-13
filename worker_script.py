from __future__ import annotations
import json
import sys
from datetime import datetime, timezone

def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "sem mensagem"
    print(json.dumps({
        "message": msg,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "status": "processed"
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
