import "maplibre-gl/dist/maplibre-gl.css";
import { Map as MapLibreMap } from "react-map-gl/maplibre";

interface MapProps {
  feedId?: string;
}

function Map(props?: MapProps) {
  const feedId = props?.feedId;
  return (
    <MapLibreMap
      mapStyle="https://demotiles.maplibre.org/style.json"
      initialViewState={{ latitude: 48.8566, longitude: 2.3522, zoom: 11 }}
      style={{ width: "100%", height: "100%", borderRadius: "0.75rem" }}
    >
      <div className="absolute bottom-4 left-4 rounded bg-slate-900/80 px-3 py-2 text-xs text-slate-200">
        {feedId ? `Feed: ${feedId}` : "Sélectionnez un feed pour afficher les données"}
      </div>
    </MapLibreMap>
  );
}

export default Map;
