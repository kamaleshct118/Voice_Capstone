import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default marker icon in react-leaflet
import L from "leaflet";
import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
    iconRetinaUrl: iconRetinaUrl,
    iconUrl: iconUrl,
    shadowUrl: shadowUrl,
});

// Assuming map_data comes in as:
// { search_location: string, center_lat: number, center_lng: number, locations: [{ name, address, lat, lng, rating }] }
interface MapComponentProps {
    mapData: {
        center_lat: number;
        center_lng: number;
        locations: Array<{
            name: string;
            address: string;
            lat: number;
            lng: number;
            rating?: number;
        }>;
    };
}

export default function MapComponent({ mapData }: MapComponentProps) {
    if (!mapData || !mapData.center_lat || !mapData.center_lng) {
        return <div className="p-4 text-center text-sm text-muted-foreground bg-muted rounded-xl bg-opacity-50">Map unavailable</div>;
    }

    const { center_lat, center_lng, locations } = mapData;

    return (
        <div className="w-full h-48 mt-3 rounded-xl overflow-hidden border border-border/60 z-10 relative">
            <MapContainer
                center={[center_lat, center_lng]}
                zoom={13}
                scrollWheelZoom={false}
                style={{ height: "100%", width: "100%" }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {locations.filter(l => l.lat && l.lng).map((loc, idx) => (
                    <Marker key={idx} position={[loc.lat, loc.lng]}>
                        <Popup>
                            <div className="text-xs font-semibold">{loc.name}</div>
                            <div className="text-[10px] text-muted-foreground">{loc.address}</div>
                            {loc.rating && <div className="text-[10px] text-amber-500 mt-1">★ {loc.rating}</div>}
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}
