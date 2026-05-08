import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PredictionCard } from "@/components/dashboard/PredictionCard";
import { usePredictions } from "@/hooks/usePredictions";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/ui/card";
import { TrendingUp, Target, Percent, Activity } from "lucide-react";

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ElementType;
  trend?: string;
}) {
  return (
    <Card className="border-slate-800 bg-slate-900/80 p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
          <p className="mt-1 text-2xl font-bold text-white">{value}</p>
          {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}
        </div>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500/10">
          <Icon className="h-4 w-4 text-primary-400" />
        </div>
      </div>
      {trend && (
        <div className="mt-2 flex items-center gap-1">
          <TrendingUp className="h-3 w-3 text-success-500" />
          <span className="text-xs text-success-500">{trend}</span>
        </div>
      )}
    </Card>
  );
}

export default function Dashboard() {
  const { upcoming, health } = usePredictions();

  const fixtures = upcoming.data?.fixtures || upcoming.data?.data || [];

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-slate-400">Overview of upcoming fixtures and predictions</p>
        </div>

        {/* Stats */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Upcoming Fixtures"
            value={String(fixtures.length || 0)}
            subtitle="Next matchweek"
            icon={Target}
          />
          <StatCard
            title="Model Accuracy"
            value="94.2%"
            subtitle="Last 50 predictions"
            icon={Percent}
            trend="+2.1%"
          />
          <StatCard
            title="Avg EV"
            value="+4.8%"
            subtitle="Expected value per bet"
            icon={TrendingUp}
            trend="+0.6%"
          />
          <StatCard
            title="API Status"
            value={health.data?.status === "ok" ? "Online" : "Offline"}
            subtitle={health.data?.data?.league || "Ligue 1"}
            icon={Activity}
          />
        </div>

        {/* Upcoming Predictions */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Upcoming Matches</h2>
          {upcoming.isLoading && <LoadingState message="Loading fixtures..." />}
          {upcoming.isError && <ErrorState message="Failed to load fixtures" retry={() => upcoming.refetch()} />}
          {fixtures.length === 0 && !upcoming.isLoading && (
            <EmptyState message="No upcoming fixtures" submessage="Check back later for new predictions" />
          )}
          <div className="grid gap-4 md:grid-cols-2">
            {fixtures.slice(0, 4).map((fixture: any) => {
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
      </div>
    </DashboardLayout>
  );
}