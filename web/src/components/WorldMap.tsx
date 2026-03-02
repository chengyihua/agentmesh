import { memo, useEffect, useState, useMemo } from 'react';
import { geoMercator, geoPath, GeoProjection } from 'd3-geo';
import { feature } from 'topojson-client';
import { Feature, Geometry } from 'geojson';

// Export projection logic to share with NetworkGraph for alignment
export const getProjection = (width: number, height: number): GeoProjection => {
  return geoMercator()
    .scale(width / 6.5)
    .translate([width / 2, height / 1.6]);
};

interface WorldMapProps {
  width?: number;
  height?: number;
}

export const WorldMap = memo(function WorldMap({ width = 1000, height = 500 }: WorldMapProps) {
  const [geographies, setGeographies] = useState<Feature<Geometry, { name: string }>[]>([]);

  useEffect(() => {
    fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch map data');
        return res.json();
      })
      .then(data => {
        // @ts-ignore - topojson-client types are tricky with generic JSON
        const countries = feature(data, data.objects.countries).features;
        setGeographies(countries);
      })
      .catch(err => console.error('Error loading map data:', err));
  }, []);

  const projection = useMemo(() => getProjection(width, height), [width, height]);
  const pathGenerator = useMemo(() => geoPath().projection(projection), [projection]);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="absolute inset-0 w-full h-full pointer-events-none select-none opacity-40"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-blue-500/20" />
          <circle cx="20" cy="20" r="0.5" fill="currentColor" className="text-blue-500/40" />
        </pattern>
        <linearGradient id="mapGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="currentColor" className="text-blue-500" stopOpacity="0.3" />
          <stop offset="100%" stopColor="currentColor" className="text-blue-600" stopOpacity="0.1" />
        </linearGradient>
      </defs>

      {/* Background Grid */}
      <rect width="100%" height="100%" fill="url(#grid)" />

      {/* World Map Paths */}
      <g>
        {geographies.map((geo, i) => (
          <path
            key={i}
            d={pathGenerator(geo) || undefined}
            fill="url(#mapGradient)"
            stroke="currentColor"
            strokeWidth="1"
            className="text-blue-400/60 transition-none"
          />
        ))}
      </g>
    </svg>
  );
});
