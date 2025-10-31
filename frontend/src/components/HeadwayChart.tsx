import { useMemo } from "react";
import { VegaLite, VisualizationSpec } from "react-vega";
import type { HeadwayRecord } from "../App";

interface HeadwayChartProps {
  data: HeadwayRecord[];
}

function HeadwayChart({ data }: HeadwayChartProps) {
  const spec = useMemo<VisualizationSpec>(() => ({
    width: "container",
    height: 320,
    mark: "bar",
    encoding: {
      x: { field: "timebin_label", type: "ordinal", title: "Tranche horaire" },
      y: { field: "departures", type: "quantitative", title: "Départs" },
      color: { field: "route_id", type: "nominal", title: "Ligne" },
      tooltip: [
        { field: "route_id", type: "nominal", title: "Ligne" },
        { field: "timebin_label", type: "ordinal", title: "Créneau" },
        { field: "departures", type: "quantitative", title: "Départs" },
        { field: "headway_p50_min", type: "quantitative", title: "p50 (min)" },
        { field: "headway_p90_min", type: "quantitative", title: "p90 (min)" }
      ]
    },
    data: { name: "table" },
    config: {
      view: { stroke: "transparent" },
      axis: { labelColor: "#e2e8f0", titleColor: "#cbd5f5" },
      legend: { labelColor: "#e2e8f0", titleColor: "#cbd5f5" }
    }
  }), []);

  if (!data.length) {
    return <p className="text-sm text-slate-400">Sélectionnez un feed pour afficher les headways.</p>;
  }

  return <VegaLite spec={spec} data={{ table: data }} actions={false} />;
}

export default HeadwayChart;
