import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useMemo, useState } from "react";
import Map from "./components/Map";
import HeadwayChart from "./components/HeadwayChart";
import FeedSelector from "./components/FeedSelector";

export type DayType = {
  day_type_id: string;
  label: string;
};

export type HeadwayRecord = {
  feed_id: string;
  day_type_id: string;
  route_id: string;
  direction_id: number | null;
  timebin_start: number;
  timebin_label: string;
  departures: number;
  headway_p50_min: number | null;
  headway_p90_min: number | null;
};

const api = axios.create({
  baseURL: "http://localhost:8000",
});

function useFeeds() {
  return useQuery({
    queryKey: ["feeds"],
    queryFn: async () => {
      const { data } = await api.get("/feeds");
      return data.feeds as Array<{ feed_id: string; provider?: string }>;
    },
  });
}

function useHeadways(feedId?: string, dayType?: string) {
  return useQuery({
    enabled: Boolean(feedId),
    queryKey: ["headways", feedId, dayType],
    queryFn: async () => {
      const { data } = await api.get("/headways", {
        params: { feed_id: feedId, day_type_id: dayType },
      });
      return data as HeadwayRecord[];
    },
  });
}

function App() {
  const { data: feeds = [] } = useFeeds();
  const [selectedFeed, setSelectedFeed] = useState<string | undefined>();
  const [selectedDayType, setSelectedDayType] = useState<string | undefined>();

  const { data: headways = [], isLoading: loadingHeadways } = useHeadways(
    selectedFeed,
    selectedDayType
  );

  const dayTypes = useMemo(() => {
    const unique = new Map<string, string>();
    headways.forEach((record) => {
      if (!unique.has(record.day_type_id)) {
        unique.set(record.day_type_id, record.day_type_id);
      }
    });
    return Array.from(unique.entries()).map(([key, label]) => ({
      day_type_id: key,
      label,
    }));
  }, [headways]);

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold">GTFS Analytics Toolkit</h1>
          <p className="text-sm text-slate-400">
            Visualisez l'offre par jour-type, créneau et ligne.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <FeedSelector feeds={feeds} value={selectedFeed} onChange={setSelectedFeed} />
          <FeedSelector
            feeds={dayTypes.map((day) => ({ feed_id: day.day_type_id, provider: day.label }))}
            value={selectedDayType}
            onChange={setSelectedDayType}
            placeholder="Jour-type"
          />
        </div>
      </header>
      <main className="grid flex-1 grid-cols-2 gap-4 overflow-hidden p-4">
        <section className="rounded-xl border border-slate-800 bg-slate-900/60">
          <Map feedId={selectedFeed} />
        </section>
        <section className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/60">
          <div className="border-b border-slate-800 px-5 py-3">
            <h2 className="text-lg font-medium">Headways (p50 / p90)</h2>
            <p className="text-xs text-slate-400">
              {loadingHeadways
                ? "Chargement des headways..."
                : `${headways.length} observations`}
            </p>
          </div>
          <div className="flex-1 overflow-auto p-5">
            <HeadwayChart data={headways} />
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
