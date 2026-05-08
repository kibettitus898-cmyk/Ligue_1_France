import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PredictionCard } from "@/components/dashboard/PredictionCard";
import { usePredictions } from "@/hooks/usePredictions";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { RefreshCw, Filter } from "lucide-react";

export default function Predictions() {
  const { upcoming, refresh } = usePredictions();
  const fixtures = upcoming.data?.fixtures || upcoming.data?.data || [];

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">All Predictions</h1>
            <p className="text-sm text-slate-400">AI-generated predictions with EV analysis</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="border-slate-700 text-slate-300 hover:bg-slate-800">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
            <Button variant="outline" size="sm" className="border-slate-700 text-slate-300 hover:bg-slate-800" onClick={refresh}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {upcoming.isLoading && <LoadingState message="Loading predictions..." />}
        {upcoming.isError && <ErrorState message="Failed to load predictions" retry={() => upcoming.refetch()} />}
        {fixtures.length === 0 && !upcoming.isLoading && (
          <EmptyState message="No predictions available" submessage="Predictions are generated before each matchweek" />
        )}
        <div className="grid gap-4 md:grid-cols-2">
          {fixtures.map((fixture: any) => {
            const bestBet = fixture.ev_analysis?.best_bet ?? null;
            const hasValue = !!fixture.ev_analysis?.has_value && !!bestBet;

            return (
              <PredictionCard
                key={fixture.fixture_id || fixture.id}
                fixture={{
                  id: fixture.fixture_id || fixture.id,
                  homeTeam: fixture.home_team || fixture.homeTeam,
                  awayTeam: fixture.away_team || fixture.awayTeam,
                  matchDate: fixture.match_date || fixture.matchDate || fixture.date,
                  venue: fixture.venue,
                }}
                prediction={{
                  homeWinProb: (fixture.probabilities?.H ?? fixture.prob_home ?? 0) * 100,
                  drawProb: (fixture.probabilities?.D ?? fixture.prob_draw ?? 0) * 100,
                  awayWinProb: (fixture.probabilities?.A ?? fixture.prob_away ?? 0) * 100,
                  confidenceScore: fixture.confidence ?? 0,
                  recommendedBet: bestBet?.outcome,
                  evValue: hasValue ? (bestBet.ev ?? 0) * 100 : 0,
                  kellyFraction: hasValue ? (bestBet.kelly_pct ?? bestBet["kelly_%"] ?? 0) : 0,
                }}
              />
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}