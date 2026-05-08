import { trpc } from "@/lib/trpc";

export function usePredictions() {
  const utils = trpc.useUtils();

  const upcoming = trpc.predictions.upcoming.useQuery(undefined, {
    staleTime: 1000 * 60 * 5,
  });

  const matches = trpc.predictions.matches.useQuery({ limit: 10 }, {
    staleTime: 1000 * 60 * 5,
  });

  const seasons = trpc.predictions.seasons.useQuery(undefined, {
    staleTime: 1000 * 60 * 60,
  });

  const health = trpc.predictions.health.useQuery(undefined, {
    staleTime: 1000 * 30,
    refetchInterval: 1000 * 30,
  });

  const refresh = () => {
    utils.predictions.upcoming.invalidate();
    utils.predictions.matches.invalidate();
  };

  return {
    upcoming,
    matches,
    seasons,
    health,
    refresh,
  };
}