import os, requests, json
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("ODDSPAPI_KEY")
BASE_URL = "https://api.oddspapi.io/v4"

print("=" * 60)
print("FETCHING NAMES FROM /odds-by-tournaments")
print("=" * 60)

url = f"{BASE_URL}/odds-by-tournaments"
params = {"apiKey": API_KEY, "bookmaker": "pinnacle", "tournamentIds": 34}

r = requests.get(url, params=params, timeout=15)
data = r.json()

print(f"Fixtures returned: {len(data)}\n")

mappings = {}
for fix in data:
    p1_id = fix.get("participant1Id")
    p2_id = fix.get("participant2Id")
    p1_name = fix.get("participant1Name", "").strip()
    p2_name = fix.get("participant2Name", "").strip()
    
    if p1_id and p1_name:
        mappings[p1_id] = p1_name
    if p2_id and p2_name:
        mappings[p2_id] = p2_name

if mappings:
    print("ID → NAME MAPPINGS (copy these into your seed script):")
    print("-" * 40)
    for pid, name in sorted(mappings.items()):
        print(f'    {pid}: "{name}",')
    print("-" * 40)
    print(f"\nTotal unique teams: {len(mappings)}")
else:
    print("❌ /odds-by-tournaments does NOT include names.")
    print("Trying /fixtures endpoint instead...")
    
    r2 = requests.get(f"{BASE_URL}/fixtures", 
                      params={"apiKey": API_KEY, "tournamentId": 34}, 
                      timeout=15)
    data2 = r2.json()
    
    for fix in data2:
        p1_id = fix.get("participant1Id")
        p2_id = fix.get("participant2Id")
        p1_name = fix.get("participant1Name", "").strip()
        p2_name = fix.get("participant2Name", "").strip()
        
        if p1_id and p1_name:
            mappings[p1_id] = p1_name
        if p2_id and p2_name:
            mappings[p2_id] = p2_name
    
    if mappings:
        print("ID → NAME MAPPINGS from /fixtures:")
        print("-" * 40)
        for pid, name in sorted(mappings.items()):
            print(f'    {pid}: "{name}",')
    else:
        print("❌ No names found. You may need to map manually using odds + fixture dates.")