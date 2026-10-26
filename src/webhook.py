
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request

app = FastAPI()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "webhook_payloads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()

    # Use the PhantomBuster execution ID to identify this payload.
    container_id = str(payload.get("containerId", ""))
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", container_id)

    if not safe_id:
        safe_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

    output_file = OUTPUT_DIR / f"phantombuster_{safe_id}.json"

    # Save the original payload so we can inspect it later.
    output_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    result = payload.get("resultObject")

    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
             result = None

    record_count = len(result) if isinstance(result, list) else None
    
    print("\n--- PhantomBuster webhook received ---")
    print(f"Agent: {payload.get('agentName', 'Unknown')}")
    print(f"Container ID: {container_id or 'Not provided'}")
    print(f"Result records: {record_count if record_count is not None else 'Not a list'}")
    print(f"Saved payload: {output_file}")

    return {
        "status": "received",
        "saved": True,
        "record_count": record_count,
    }
