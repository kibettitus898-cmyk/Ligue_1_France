# discover_participants.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDSPAPI_KEY")
BASE_URL = "https://api.oddspapi.io/v4"

# The 18 IDs from your logs
IDS = [1641, 1643, 1644, 1646, 1647, 1648, 1649, 1651, 1653, 1656, 1658, 1659, 1661, 1662, 1681, 1684, 1715, 6070]

def try_endpoint(url, params, label):
    try:
        r = requests.get(url, params=params, timeout=15)
        print(f"\n{label}: {r.status_code}")
        print(f"URL: {r.request.url}")
        if r.status_code == 200:
            data = r.json()
            print(f"Response type: {type(data)}")
            print(json.dumps(data, indent=2)[:2000])
            return data
    except Exception as e:
        print(f"{label} failed: {e}")
    return None

# Try various endpoint patterns
print("=" * 60)
print("DISCOVERING PARTICIPANT NAMES")
print("=" * 60)

# 1. Try /participants with sportId
try_endpoint(f"{BASE_URL}/participants", {"apiKey": API_KEY, "sportId": 10}, "1. /participants?sportId=10")

# 2. Try /participants with tournamentId
try_endpoint(f"{BASE_URL}/participants", {"apiKey": API_KEY, "tournamentId": 34}, "2. /participants?tournamentId=34")

# 3. Try /participants with ids
ids_str = ",".join(map(str, IDS))
try_endpoint(f"{BASE_URL}/participants", {"apiKey": API_KEY, "participantIds": ids_str}, "3. /participants?participantIds=...")

# 4. Try /participants/{id} for first ID
try_endpoint(f"{BASE_URL}/participants/{IDS[0]}", {"apiKey": API_KEY}, f"4. /participants/{IDS[0]}")

# 5. Try /fixtures to see raw structure
try_endpoint(f"{BASE_URL}/fixtures", {"apiKey": API_KEY, "tournamentId": 34}, "5. /fixtures?tournamentId=34")

# 6. Try /odds-by-tournaments raw
try_endpoint(f"{BASE_URL}/odds-by-tournaments", {"apiKey": API_KEY, "tournamentIds": 34, "bookmaker": "pinnacle"}, "6. /odds-by-tournaments")