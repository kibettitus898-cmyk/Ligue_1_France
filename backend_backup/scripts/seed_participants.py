import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.core.supabase_client import get_supabase

# All 18 IDs from your upcoming fixtures (from /fixtures endpoint)
SEED = {
    1641: "Olympique Marseille",
    1643: "Lille OSC",
    1644: "Paris Saint-Germain",
    1646: "AJ Auxerre",
    1647: "FC Nantes",
    1648: "Racing Club De Lens",
    1649: "Olympique Lyon",
    1651: "FC Metz",
    1653: "AS Monaco",
    1656: "FC Lorient",
    1658: "Stade Rennais FC",
    1659: "Strasbourg Alsace",
    1661: "OGC Nice",
    1662: "Le Havre AC",
    1681: "Toulouse FC",
    1684: "Angers SCO",
    1715: "Stade Brest 29",
    6070: "Paris FC",
}

def main():
    supabase = get_supabase()
    rows = [
        {"id": k, "name": v, "tournament_id": 34}
        for k, v in SEED.items()
    ]
    supabase.table("participant_names").upsert(rows, on_conflict="id").execute()
    print(f"Seeded {len(rows)} participants")

if __name__ == "__main__":
    main()