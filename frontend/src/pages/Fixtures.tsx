import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { usePredictions } from "@/hooks/usePredictions";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CalendarDays, MapPin, ArrowRight } from "lucide-react";

export default function Fixtures() {
  const { upcoming } = usePredictions();
  const fixtures = upcoming.data?.fixtures || upcoming.data?.data || [];

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Fixtures</h1>
          <p className="text-sm text-slate-400">Upcoming Ligue 1 match schedule</p>
        </div>

        {upcoming.isLoading && <LoadingState message="Loading fixtures..." />}
        {upcoming.isError && <ErrorState message="Failed to load fixtures" retry={() => upcoming.refetch()} />}
        {fixtures.length === 0 && !upcoming.isLoading && (
          <EmptyState message="No fixtures found" submessage="Check back later for upcoming matches" />
        )}

        <div className="space-y-3">
          {fixtures.map((fixture: any) => {
            const date = fixture.match_date || fixture.matchDate || fixture.date;
            return (
              <Card key={fixture.fixture_id || fixture.id} className="border-slate-800 bg-slate-900/80 p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4 flex-1">
                    <div className="flex flex-col items-center gap-1 min-w-[60px]">
                      <span className="text-xs text-slate-500">
                        {date ? new Date(date).toLocaleDateString("en-GB", { day: "numeric", month: "short" }) : "TBD"}
                      </span>
                      <span className="text-xs text-primary-400 font-semibold">
                        {date ? new Date(date).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }) : ""}
                      </span>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-white">{fixture.home_team || fixture.homeTeam}</span>
                        <ArrowRight className="h-3 w-3 text-slate-500" />
                        <span className="text-sm font-semibold text-white">{fixture.away_team || fixture.awayTeam}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1">
                        <div className="flex items-center gap-1 text-xs text-slate-500">
                          <MapPin className="h-3 w-3" />
                          {fixture.venue || "TBD"}
                        </div>
                        <div className="flex items-center gap-1 text-xs text-slate-500">
                          <CalendarDays className="h-3 w-3" />
                          {fixture.season || "2024/25"}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="border-slate-700 text-slate-400 text-xs">
                      {fixture.status || "Scheduled"}
                    </Badge>
                    {fixture.prediction && (
                      <Badge className="bg-primary-500/10 text-primary-400 text-xs">
                        Predicted
                      </Badge>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}
