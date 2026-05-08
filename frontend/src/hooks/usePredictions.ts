import { useQuery } from "@tanstack/react-query";

const HF_API_URL = import.meta.env.VITE_HF_API_URL || "https://otito256-ligua1.hf.space";

async function fetchUpcoming() {
  const res = await fetch(`${HF_API_URL}/api/v1/predict/upcoming`);
  if (!res.ok) throw new Error("Failed to fetch predictions");
  return res.json();
}

async function fetchMatches(limit = 10) {
  const res = await fetch(`${HF_API_URL}/api/v1/matches?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch matches");
  return res.json();
}

async function fetchSeasons() {
  const res = await fetch(`${HF_API_URL}/api/v1/matches/seasons`);
  if (!res.ok) throw new Error("Failed to fetch seasons");
  return res.json();
}

async function fetchHealth() {
  const res = await fetch(`${HF_API_URL}/health`);
  if (!res.ok) throw new Error("API health check failed");
  return res.json();
}

export function usePredictions() {
  const upcoming = useQuery({
    queryKey: ["upcoming"],
    queryFn: fetchUpcoming,
    staleTime: 1000 * 60 * 5,
  });

  const matches = useQuery({
    queryKey: ["matches"],
    queryFn: () => fetchMatches(10),
    staleTime: 1000 * 60 * 5,
  });

  const seasons = useQuery({
    queryKey: ["seasons"],
    queryFn: fetchSeasons,
    staleTime: 1000 * 60 * 60,
  });

  const health = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    staleTime: 1000 * 30,
    refetchInterval: 1000 * 30,
  });

  const refresh = () => {
    upcoming.refetch();
    matches.refetch();
  };

  return {
    upcoming,
    matches,
    seasons,
    health,
    refresh,
  };
}