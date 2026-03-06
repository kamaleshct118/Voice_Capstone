import { useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Phone, Clock, Globe, MapPin, Navigation } from "lucide-react";

// Fix default marker icon for react-leaflet
import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl });

// Custom red hospital marker
const hospitalIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
});

// Blue marker for user location
const userIcon = new L.Icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
});

interface Clinic {
    name: string;
    address: string;
    lat: number;
    lng: number;
    distance_km?: number;
    phone?: string;
    opening_hours?: string;
    website?: string;
    type?: string;
}

interface MapComponentProps {
    mapData: {
        center_lat: number;
        center_lng: number;
        search_location?: string;
        locations: Clinic[];
    };
}

// Helper: fly to marker on list item click
function FlyTo({ lat, lng }: { lat: number; lng: number }) {
    const map = useMap();
    map.flyTo([lat, lng], 16, { duration: 0.8 });
    return null;
}

export default function MapComponent({ mapData }: MapComponentProps) {
    const [flyTarget, setFlyTarget] = useState<{ lat: number; lng: number } | null>(null);

    if (!mapData?.center_lat || !mapData?.center_lng) {
        return (
            <div className="p-4 text-center text-sm text-muted-foreground bg-muted rounded-xl">
                Map unavailable
            </div>
        );
    }

    const { center_lat, center_lng, locations = [] } = mapData;
    const validLocations = locations.filter((l) => l.lat && l.lng);

    return (
        <div className="space-y-3">
            {/* ── Interactive Map ───────────────────────────────────── */}
            <div className="w-full h-56 rounded-xl overflow-hidden border border-border/60 relative z-10">
                <MapContainer
                    center={[center_lat, center_lng]}
                    zoom={14}
                    scrollWheelZoom={false}
                    style={{ height: "100%", width: "100%" }}
                >
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {/* User location marker */}
                    <Marker position={[center_lat, center_lng]} icon={userIcon}>
                        <Popup>
                            <div className="text-xs font-semibold text-blue-600">📍 Your Location</div>
                        </Popup>
                    </Marker>

                    {/* Hospital markers */}
                    {validLocations.map((loc, idx) => (
                        <Marker key={idx} position={[loc.lat, loc.lng]} icon={hospitalIcon}>
                            <Popup maxWidth={220}>
                                <div className="space-y-1 text-xs">
                                    <div className="font-bold text-red-600 text-sm">{loc.name}</div>
                                    {loc.distance_km !== undefined && (
                                        <div className="text-gray-500">📏 {loc.distance_km} km away</div>
                                    )}
                                    {loc.phone && loc.phone !== "N/A" && (
                                        <div className="text-gray-600">📞 {loc.phone}</div>
                                    )}
                                    {loc.opening_hours && (
                                        <div className="text-gray-500">🕐 {loc.opening_hours}</div>
                                    )}
                                    {loc.address && loc.address !== "See map for location" && (
                                        <div className="text-gray-500 text-[10px] mt-1">{loc.address}</div>
                                    )}
                                    {loc.website && (
                                        <a
                                            href={loc.website}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-500 text-[10px] underline"
                                        >
                                            Visit website →
                                        </a>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                    ))}

                    {/* Fly animation when a list item is clicked */}
                    {flyTarget && <FlyTo lat={flyTarget.lat} lng={flyTarget.lng} />}
                </MapContainer>
            </div>

            {/* ── Hospital List Panel ───────────────────────────────── */}
            {validLocations.length > 0 && (
                <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                        <MapPin className="w-3 h-3 text-red-400" />
                        {validLocations.length} Nearby Facilities
                    </p>
                    <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1 scrollbar-thin">
                        {validLocations.map((loc, idx) => (
                            <button
                                key={idx}
                                onClick={() => setFlyTarget({ lat: loc.lat, lng: loc.lng })}
                                className="w-full text-left flex items-start gap-3 p-2.5 rounded-xl bg-muted/40 hover:bg-muted/70 border border-border/40 hover:border-red-500/30 transition-all group"
                            >
                                {/* Index badge */}
                                <span className="shrink-0 w-6 h-6 rounded-md bg-red-500/15 text-red-400 text-xs font-bold flex items-center justify-center mt-0.5 group-hover:bg-red-500/25">
                                    {idx + 1}
                                </span>

                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-foreground truncate leading-snug">
                                        {loc.name}
                                    </p>
                                    <div className="flex flex-wrap gap-x-2 gap-y-0.5 mt-0.5">
                                        {loc.distance_km !== undefined && (
                                            <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                                                <Navigation className="w-2.5 h-2.5" />
                                                {loc.distance_km} km
                                            </span>
                                        )}
                                        {loc.phone && loc.phone !== "N/A" && (
                                            <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                                                <Phone className="w-2.5 h-2.5" />
                                                {loc.phone}
                                            </span>
                                        )}
                                        {loc.opening_hours && (
                                            <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                                                <Clock className="w-2.5 h-2.5" />
                                                {loc.opening_hours.length > 20
                                                    ? loc.opening_hours.slice(0, 20) + "…"
                                                    : loc.opening_hours}
                                            </span>
                                        )}
                                    </div>
                                    {loc.address && loc.address !== "See map for location" && (
                                        <p className="text-[10px] text-muted-foreground/70 truncate mt-0.5">
                                            {loc.address}
                                        </p>
                                    )}
                                </div>

                                <MapPin className="w-3.5 h-3.5 text-red-400/60 shrink-0 mt-1 group-hover:text-red-400 transition-colors" />
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
