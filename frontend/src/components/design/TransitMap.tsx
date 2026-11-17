import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { VehiclePosition } from '../../lib/useLiveTelemetry';

interface TransitMapProps {
  vehicles: VehiclePosition[];
  polyline?: [number, number][];
  routeColor?: string;
  stops?: { id: string; code: string; name: string; lat: number; lng: number }[];
  onSelectVehicle?: (veh: VehiclePosition) => void;
  onSelectStop?: (stop: any) => void;
  className?: string;
  center?: [number, number];
  zoom?: number;
}

export const TransitMap: React.FC<TransitMapProps> = ({
  vehicles,
  polyline,
  routeColor = '#2563EB',
  stops = [],
  onSelectVehicle,
  onSelectStop,
  className = 'h-[360px] w-full',
  center = [25.445, 81.838], // Prayagraj centroid
  zoom = 13,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<{ [key: string]: L.Marker }>({});
  const polylineLayerRef = useRef<L.Polyline | null>(null);
  const stopMarkersRef = useRef<L.Marker[]>([]);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Create map with muted transit styling per SPEC §9.2
    const map = L.map(mapContainerRef.current, {
      center,
      zoom,
      zoomControl: true,
      attributionControl: false,
    });

    // Muted OpenStreetMap Cartography
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      className: 'transit-map-tiles',
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Route Polyline
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (polylineLayerRef.current) {
      map.removeLayer(polylineLayerRef.current);
      polylineLayerRef.current = null;
    }

    if (polyline && polyline.length > 1) {
      const latlngs = polyline.map((p) => [p[0], p[1]] as [number, number]);
      const line = L.polyline(latlngs, {
        color: routeColor,
        weight: 5,
        opacity: 0.85,
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(map);
      polylineLayerRef.current = line;
      map.fitBounds(line.getBounds(), { padding: [25, 25] });
    }
  }, [polyline, routeColor]);

  // Update Stop Markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear previous stop markers
    stopMarkersRef.current.forEach((m) => map.removeLayer(m));
    stopMarkersRef.current = [];

    stops.forEach((s) => {
      const icon = L.divIcon({
        className: 'custom-stop-marker',
        html: `
          <div style="
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #FFFFFF;
            border: 3px solid #1C1B19;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            cursor: pointer;
          " title="${s.name} (${s.code})"></div>
        `,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      const marker = L.marker([s.lat, s.lng], { icon })
        .addTo(map)
        .bindPopup(`<strong>${s.name}</strong><br><span style="font-family:monospace">${s.code}</span>`);

      if (onSelectStop) {
        marker.on('click', () => onSelectStop(s));
      }
      stopMarkersRef.current.push(marker);
    });
  }, [stops, onSelectStop]);

  // Update Vehicle Markers smoothly (SPEC §9.5 CSS transition)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    vehicles.forEach((v) => {
      const iconHtml = `
        <div style="
          display: flex;
          align-items: center;
          gap: 4px;
          background: #1C1B19;
          color: #FFFFFF;
          padding: 2px 6px;
          border-radius: 4px;
          border: 2px solid ${v.color_hex || '#E8A200'};
          font-family: monospace;
          font-size: 11px;
          font-weight: bold;
          white-space: nowrap;
          box-shadow: 0 2px 5px rgba(0,0,0,0.35);
          cursor: pointer;
        ">
          <span style="display:inline-block; transform: rotate(${v.heading}deg);">▶</span>
          <span>${v.route_code || 'BUS'}</span>
        </div>
      `;

      const icon = L.divIcon({
        className: 'vehicle-live-marker',
        html: iconHtml,
        iconSize: [50, 22],
        iconAnchor: [25, 11],
      });

      if (markersRef.current[v.vehicle_id]) {
        // Move existing marker smoothly
        const existing = markersRef.current[v.vehicle_id];
        existing.setLatLng([v.lat, v.lng]);
        existing.setIcon(icon);
      } else {
        // Create new marker
        const marker = L.marker([v.lat, v.lng], { icon })
          .addTo(map)
          .bindPopup(`
            <div style="font-size:12px; font-family:sans-serif;">
              <strong>${v.fleet_no}</strong> (${v.route_code})<br/>
              Speed: ${v.speed_kmph} km/h • Heading: ${v.heading}°<br/>
              Occupancy: <strong>${v.occupancy}</strong><br/>
              Delay: ${v.delay_s > 0 ? `+${Math.round(v.delay_s / 60)}m` : 'On time'}
            </div>
          `);

        if (onSelectVehicle) {
          marker.on('click', () => onSelectVehicle(v));
        }
        markersRef.current[v.vehicle_id] = marker;
      }
    });
  }, [vehicles, onSelectVehicle]);

  return (
    <div className={`rounded-[4px] border border-[var(--rule)] overflow-hidden shadow-xs relative ${className}`}>
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
};
