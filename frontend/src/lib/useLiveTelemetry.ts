import { useEffect, useRef } from 'react';

export interface VehiclePosition {
  vehicle_id: string;
  fleet_no: string;
  route_id: string;
  route_code: string;
  color_hex: string;
  lat: number;
  lng: number;
  heading: number;
  speed_kmph: number;
  occupancy: string;
  delay_s: number;
  ts: number;
}

export function useLiveTelemetry(onPositions: (positions: VehiclePosition[]) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  useEffect(() => {
    let isMounted = true;

    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//localhost:8000/ws/live`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        // Subscribe to routes & stops
        ws.send(JSON.stringify({ subscribe: { routes: ['*'], stops: ['*'] } }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'positions' && Array.isArray(msg.data)) {
            onPositions(msg.data);
          }
        } catch (e) {
          console.error('Error parsing WS message:', e);
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);
}
