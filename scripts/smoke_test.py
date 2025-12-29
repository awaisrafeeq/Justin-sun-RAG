import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from app.main import app

TEST_FEED_URL = "https://lexfridman.com/feed/podcast/"


def main():
    client = TestClient(app)

    health = client.get("/health")
    print("HEALTH", health.status_code, health.json())

    feed_resp = client.post("/api/feeds", json={"url": TEST_FEED_URL})
    print("FEED POST", feed_resp.status_code)
    feed_data = feed_resp.json()
    print(json.dumps(feed_data, indent=2))

    feed_id = feed_data["id"]
    episodes = client.get(f"/api/feeds/{feed_id}/episodes")
    print("EPISODES", episodes.status_code, len(episodes.json()))


if __name__ == "__main__":
    main()
