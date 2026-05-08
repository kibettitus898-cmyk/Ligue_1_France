import { Calendar, MapPin, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { EVBadge } from "./EVBadge";
import { ConfidenceMeter } from "./ConfidenceMeter";
import { KellyIndicator } from "./KellyIndicator";
import { cn } from "@/lib/utils";

interface PredictionCardProps {
  fixture: {
    id: string | number;
    homeTeam: string;
    awayTeam: string;
    homeTeamLogo?: string;
    awayTeamLogo?: string;
    matchDate: string;
    venue?: string;
  };
  prediction?: {
    homeWinProb?: number;
    drawProb?: number;
    awayWinProb?: number;
    confidenceScore?: number;
    recommendedBet?: string;
    evValue?: number;
    kellyFraction?: number;
    expectedGoalsHome?: number;
    expectedGoalsAway?: number;
  };
  odds?: {
    homeOdds?: number;
    drawOdds?: number;
    awayOdds?: number;
  };
  className?: string;
}

export function PredictionCard({ fixture, prediction, odds, className }: PredictionCardProps) {
  const hasPrediction = !!prediction;
  const ev = prediction?.evValue ?? 0;
  const isValueBet = ev > 0;

  const probs = {
    home: prediction?.homeWinProb ?? 33,
    draw: prediction?.drawProb ?? 33,
    away: prediction?.awayWinProb ?? 34,
  };

  const maxProb = Math.max(probs.home, probs.draw, probs.away);
  const fav = probs.home === maxProb ? "home" : probs.away === maxProb ? "away" : "draw";

  return (
    <Card className={cn("relative overflow-hidden border-slate-800 bg-slate-900/80 p-4", isValueBet && "ring-1 ring-success-500/20", className)}>
      {isValueBet && (
        <div className="absolute -top-px left-4 right-4 h-px bg-gradient-to-r from-transparent via-success-500/50 to-transparent" />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Calendar className="h-3 w-3" />
          {fixture.matchDate ? new Date(fixture.matchDate).toLocaleDateString("en-GB", {
            weekday: "short",
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
          }) : "TBD"}
        </div>
        {fixture.venue && (
          <div className="flex items-center gap-1 text-xs text-slate-500">
            <MapPin className="h-3 w-3" />
            {fixture.venue}
          </div>
        )}
      </div>

      {/* Teams */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-900/50 text-xs font-bold text-primary-300">
            {fixture.homeTeamLogo ? (
              <img src={fixture.homeTeamLogo} alt={fixture.homeTeam} className="h-6 w-6 object-contain" />
            ) : (
              fixture.homeTeam.slice(0, 3).toUpperCase()
            )}
          </div>
          <div>
            <p className="text-sm font-semibold text-white">{fixture.homeTeam}</p>
            {odds?.homeOdds && <p className="text-xs text-slate-500">@{odds.homeOdds}</p>}
          </div>
        </div>

        <div className="text-center px-4">
          <span className="text-xs text-slate-500">VS</span>
        </div>

        <div className="flex items-center gap-3 flex-1 justify-end text-right">
          <div>
            <p className="text-sm font-semibold text-white">{fixture.awayTeam}</p>
            {odds?.awayOdds && <p className="text-xs text-slate-500">@{odds.awayOdds}</p>}
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-900/50 text-xs font-bold text-primary-300">
            {fixture.awayTeamLogo ? (
              <img src={fixture.awayTeamLogo} alt={fixture.awayTeam} className="h-6 w-6 object-contain" />
            ) : (
              fixture.awayTeam.slice(0, 3).toUpperCase()
            )}
          </div>
        </div>
      </div>

      {/* Probabilities */}
      {hasPrediction && (
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className={cn("rounded-lg p-2 text-center", fav === "home" ? "bg-primary-500/10 ring-1 ring-primary-500/20" : "bg-slate-800/50")}>
            <p className="text-sm font-bold text-white">{probs.home.toFixed(0)}%</p>
            <p className="text-[10px] text-slate-400">Home</p>
          </div>
          <div className={cn("rounded-lg p-2 text-center", fav === "draw" ? "bg-accent-500/10 ring-1 ring-accent-500/20" : "bg-slate-800/50")}>
            <p className="text-sm font-bold text-white">{probs.draw.toFixed(0)}%</p>
            <p className="text-[10px] text-slate-400">Draw</p>
          </div>
          <div className={cn("rounded-lg p-2 text-center", fav === "away" ? "bg-primary-500/10 ring-1 ring-primary-500/20" : "bg-slate-800/50")}>
            <p className="text-sm font-bold text-white">{probs.away.toFixed(0)}%</p>
            <p className="text-[10px] text-slate-400">Away</p>
          </div>
        </div>
      )}

      {/* Prediction details */}
      {hasPrediction && (
        <div className="space-y-3">
          {prediction?.recommendedBet && (
            <div className="flex items-center justify-between rounded-lg bg-slate-800/50 p-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-success-500" />
                <span className="text-sm text-white">{prediction.recommendedBet}</span>
              </div>
              <EVBadge ev={ev} />
            </div>
          )}

          <div className="flex items-center justify-between">
            <div className="flex-1 pr-4">
              <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Confidence</p>
              <ConfidenceMeter value={prediction?.confidenceScore ?? 50} />
            </div>
            <KellyIndicator fraction={prediction?.kellyFraction ?? 0} />
          </div>

          {(prediction?.expectedGoalsHome || prediction?.expectedGoalsAway) && (
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>xG: {fixture.homeTeam} {prediction.expectedGoalsHome?.toFixed(2)}</span>
              <span>xG: {fixture.awayTeam} {prediction.expectedGoalsAway?.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}

      {!hasPrediction && (
        <div className="py-4 text-center">
          <p className="text-sm text-slate-500">Prediction pending</p>
        </div>
      )}
    </Card>
  );
}
