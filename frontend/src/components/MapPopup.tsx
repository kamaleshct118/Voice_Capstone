import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { X } from "lucide-react";
import L from "leaflet";
import type { MapData } from "@/types/clinical";

// Fix default marker icons for leaflet in bundled apps
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

interface MapPopupProps {
  data: MapData;
  onClose: () => void;
}

const MapPopup = ({ data, onClose }: MapPopupProps) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current).setView([data.lat, data.lng], 15);
    mapInstanceRef.current = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    const popupContent = `<strong>${data.name}</strong>${data.contact ? `<br/>${data.contact}` : ""}`;
    L.marker([data.lat, data.lng]).addTo(map).bindPopup(popupContent).openPopup();

    // Force re-render tiles
    setTimeout(() => map.invalidateSize(), 100);

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [data]);

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/40 backdrop-blur-sm p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="clinical-card-elevated w-full max-w-lg overflow-hidden"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h3 className="font-semibold text-foreground">{data.name}</h3>
            {data.contact && <p className="text-sm text-muted-foreground">{data.contact}</p>}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div ref={mapRef} className="h-80 w-full" />
      </motion.div>
    </motion.div>
  );
};

export default MapPopup;
