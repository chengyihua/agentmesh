import { useEffect, useRef, useMemo, useState } from 'react';
import { useAgents, useStats } from '@/hooks/useRegistry';
import { Agent } from '@/types/agent';
import { WorldMap, getProjection } from './WorldMap';

interface Node extends Agent {
    x: number;
    y: number;
    region: string;
    color: string;
    size: number;
    glow: boolean;
    targetX: number; // For animation
    targetY: number;
}

interface Link {
    source: Node;
    target: Node;
}

interface Beam {
    id: string;
    source: Node;
    target: Node;
    progress: number;
    speed: number;
    color: string;
}

// Real geographic coordinates for regions
const REGIONS: Record<string, { lat: number, lng: number, color: string, name: string }> = {
    'na-east': { lat: 38.8, lng: -77.0, color: '#3b82f6', name: 'N. Virginia' }, // US East
    'na-west': { lat: 45.5, lng: -122.6, color: '#60a5fa', name: 'Oregon' }, // US West
    'eu-west': { lat: 51.5, lng: -0.1, color: '#10b981', name: 'London' }, // UK
    'eu-central': { lat: 50.1, lng: 8.6, color: '#34d399', name: 'Frankfurt' }, // Germany
    'ap-southeast': { lat: 1.3, lng: 103.8, color: '#f59e0b', name: 'Singapore' }, // Singapore
    'ap-northeast': { lat: 35.6, lng: 139.6, color: '#ef4444', name: 'Tokyo' }, // Japan
    'sa-east': { lat: -23.5, lng: -46.6, color: '#8b5cf6', name: 'São Paulo' }, // Brazil
    'au-southeast': { lat: -33.8, lng: 151.2, color: '#ec4899', name: 'Sydney' }, // Australia
};

export function NetworkGraph() {
    const { data: agents = [] } = useAgents({ limit: 1000 });
    const { data: stats } = useStats({ refetchInterval: 2000 });
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
    const [dimensions, setDimensions] = useState({ width: 1200, height: 600 });

    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const updateDimensions = () => {
            if (containerRef.current) {
                const { clientWidth, clientHeight } = containerRef.current;
                setDimensions({ width: clientWidth, height: clientHeight });
                
                if (canvasRef.current) {
                    // Set actual canvas resolution to match display size for sharp rendering
                    canvasRef.current.width = clientWidth;
                    canvasRef.current.height = clientHeight;
                }
            }
        };

        updateDimensions();
        window.addEventListener('resize', updateDimensions);
        return () => window.removeEventListener('resize', updateDimensions);
    }, []);

    // Prepare Graph Data
    const graphData = useMemo(() => {
        if (!agents.length) return { nodes: [], links: [] };

        const { width, height } = dimensions;
        const projection = getProjection(width, height);

        // Sort agents by trust score to determine ranking
        const sortedAgents = [...agents].sort((a, b) => (b.trust_score || 0) - (a.trust_score || 0));
        const totalAgents = agents.length;

        // 1. Create Nodes with Geo-Distribution
        const nodes: Node[] = agents.map((agent, i) => {
            // Deterministic hash
            const hash = agent.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
            
            // Assign to region based on hash
            const regionKeys = Object.keys(REGIONS);
            const regionKey = regionKeys[hash % regionKeys.length];
            const region = REGIONS[regionKey];

            // Project lat/lng to x/y
            const [baseX, baseY] = projection([region.lng, region.lat]) || [0, 0];

            // Gaussian distribution around region center
            // Box-Muller transform for normal distribution
            const u = 1 - Math.random();
            const v = Math.random();
            const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
            const spread = 20; // Pixel spread

            const x = baseX + (z * spread);
            const y = baseY + (Math.sqrt(-2.0 * Math.log(u)) * Math.sin(2.0 * Math.PI * v) * spread);

            const isHealthy = !agent.health_status || agent.health_status === 'healthy';
            
            // Determine styling based on rank
            const rank = sortedAgents.findIndex(a => a.id === agent.id);
            const percentile = rank / totalAgents;
            
            // Base size on trust score (range 1.5-3)
            const score = agent.trust_score || 0;
            let size = 1.5 + (score * 1.5); 
            let color = isHealthy ? region.color : '#ef4444';
            let glow = false;

            if (isHealthy) {
                if (rank < 3) { // Top 3 - Gold Tier
                    size = 6; // Reduced from 12
                    color = '#fbbf24'; // Amber-400 (Gold)
                    glow = true;
                } else if (percentile <= 0.10) { // Top 10% - Silver Tier
                    size = 4; // Reduced from 8
                    color = '#e2e8f0'; // Slate-200 (Silver)
                    glow = true;
                } else if (percentile <= 0.25) { // Top 25% - Bronze Tier
                    size = 2.5; // Reduced from 6
                    color = '#f59e0b'; // Amber-500 (Bronze/Orange)
                }
                // Others keep region color and score-based size
            }

            return {
                ...agent,
                x,
                y,
                size,
                glow,
                targetX: x,
                targetY: y,
                region: region.name,
                color // Red if unhealthy
            };
        });

        // 2. Create Links (Inter-region and Intra-region)
        const links: Link[] = [];
        const regionGroups: Record<string, Node[]> = {};
        
        nodes.forEach(node => {
            if (!regionGroups[node.region]) regionGroups[node.region] = [];
            regionGroups[node.region].push(node);
        });

        // Connect nodes
        nodes.forEach((node, i) => {
            // 1. Intra-region connections (Local LAN)
            const peers = regionGroups[node.region];
            if (peers.length > 1) {
                // Connect to nearest neighbor
                let minDist = Infinity;
                let nearest: Node | null = null;
                peers.forEach(peer => {
                    if (peer === node) return;
                    const d = Math.hypot(peer.x - node.x, peer.y - node.y);
                    if (d < minDist) {
                        minDist = d;
                        nearest = peer;
                    }
                });
                if (nearest) links.push({ source: node, target: nearest });
            }

            // 2. Inter-region backbone (WAN) - Random long links
            if (Math.random() > 0.98) { // 2% chance to be a gateway
                const otherRegions = Object.keys(regionGroups).filter(r => r !== node.region);
                const targetRegion = otherRegions[Math.floor(Math.random() * otherRegions.length)];
                const targetPeers = regionGroups[targetRegion];
                if (targetPeers && targetPeers.length > 0) {
                    const target = targetPeers[Math.floor(Math.random() * targetPeers.length)];
                    links.push({ source: node, target });
                }
            }
        });

        return { nodes, links };
    }, [agents, dimensions]);

    // Stable reference for animation loop to avoid restarting it on data changes
    const graphDataRef = useRef(graphData);
    const dimensionsRef = useRef(dimensions);

    useEffect(() => {
        graphDataRef.current = graphData;
    }, [graphData]);

    useEffect(() => {
        dimensionsRef.current = dimensions;
    }, [dimensions]);

    // Animation Loop
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d', { alpha: false }); // Optimize for no transparency if possible (but we use it)
        if (!ctx) return;

        let beams: Beam[] = [];
        let animationFrameId: number;
        let frameCount = 0;

        const tick = () => {
            frameCount++;
            const { width, height } = dimensionsRef.current;
            const { nodes, links } = graphDataRef.current;

            // Canvas size is controlled by props, so just clear based on dimensions
            ctx.clearRect(0, 0, width, height);

            // World Map is now handled by the SVG background component
            
            // 1. Draw Links (Batch Rendering for Performance)
            // Batch 1: Short distance (Local)
            ctx.beginPath();
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
            ctx.lineWidth = 0.5;
            
            links.forEach(link => {
                const dist = Math.hypot(link.target.x - link.source.x, link.target.y - link.source.y);
                if (dist <= 100) {
                    ctx.moveTo(link.source.x, link.source.y);
                    ctx.lineTo(link.target.x, link.target.y);
                }
            });
            ctx.stroke();

            // Batch 2: Long distance (WAN)
            ctx.beginPath();
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
            ctx.lineWidth = 1;
            
            links.forEach(link => {
                const dist = Math.hypot(link.target.x - link.source.x, link.target.y - link.source.y);
                if (dist > 100) {
                    const midX = (link.source.x + link.target.x) / 2;
                    const midY = (link.source.y + link.target.y) / 2 - 50; 
                    ctx.moveTo(link.source.x, link.source.y);
                    ctx.quadraticCurveTo(midX, midY, link.target.x, link.target.y);
                }
            });
            ctx.stroke();

            // 2. Draw Nodes (Grouped by Glow vs No-Glow to minimize state changes)
            
            // Draw standard nodes (no glow, simple circle)
            nodes.forEach(node => {
                if (node.glow) return; // Skip glow nodes for next pass
                
                ctx.beginPath();
                ctx.fillStyle = node.color;
                ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
                ctx.fill();
            });

            // Draw glowing nodes (expensive, so do them last and fewer of them)
            nodes.forEach(node => {
                if (!node.glow) return;

                ctx.save();
                ctx.fillStyle = node.color;
                ctx.shadowBlur = 15; // Slightly reduced
                ctx.shadowColor = node.color;
                
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
                ctx.fill();
                
                // Ring for high-ranking
                if (node.size >= 4) {
                    ctx.strokeStyle = 'rgba(255,255,255,0.5)';
                    ctx.lineWidth = 1;
                    ctx.shadowBlur = 0; // Turn off shadow for ring
                    ctx.stroke();
                }
                ctx.restore();
            });

            // Random pulse effect (Optimized: Batch draw)
            // ... (Removing pulse for now to save FPS, or simplify it)


            // 3. Traffic Simulation (Beams)
            if (frameCount % 3 === 0) { // More frequent for beams
                const link = links[Math.floor(Math.random() * links.length)];
                if (link) {
                    beams.push({
                        id: Math.random().toString(),
                        source: link.source,
                        target: link.target,
                        progress: 0,
                        speed: 0.02 + Math.random() * 0.04, // Fast communication
                        color: link.source.color
                    });
                }
            }

            // Update & Draw Beams
            for (let i = beams.length - 1; i >= 0; i--) {
                const b = beams[i];
                b.progress += b.speed;
                if (b.progress >= 1) {
                    beams.splice(i, 1);
                    continue;
                }

                const dist = Math.hypot(b.target.x - b.source.x, b.target.y - b.source.y);
                const isLongDistance = dist > 100;
                
                // Calculate current position
                let x, y;
                if (isLongDistance) {
                     const midX = (b.source.x + b.target.x) / 2;
                     const midY = (b.source.y + b.target.y) / 2 - 50;
                     const t = b.progress;
                     const invT = 1 - t;
                     x = invT * invT * b.source.x + 2 * invT * t * midX + t * t * b.target.x;
                     y = invT * invT * b.source.y + 2 * invT * t * midY + t * t * b.target.y;
                } else {
                    x = b.source.x + (b.target.x - b.source.x) * b.progress;
                    y = b.source.y + (b.target.y - b.source.y) * b.progress;
                }

                // Draw "Comet" Trail
                const trailLength = 0.15;
                const trailStart = Math.max(0, b.progress - trailLength);
                
                // Trail start point (tail)
                let tailX, tailY;
                if (isLongDistance) {
                     const midX = (b.source.x + b.target.x) / 2;
                     const midY = (b.source.y + b.target.y) / 2 - 50;
                     const t = trailStart;
                     const invT = 1 - t;
                     tailX = invT * invT * b.source.x + 2 * invT * t * midX + t * t * b.target.x;
                     tailY = invT * invT * b.source.y + 2 * invT * t * midY + t * t * b.target.y;
                } else {
                    tailX = b.source.x + (b.target.x - b.source.x) * trailStart;
                    tailY = b.source.y + (b.target.y - b.source.y) * trailStart;
                }

                // Draw gradient line
                const gradient = ctx.createLinearGradient(tailX, tailY, x, y);
                gradient.addColorStop(0, 'rgba(255, 255, 255, 0)');
                gradient.addColorStop(1, b.color); // Head color

                ctx.strokeStyle = gradient;
                ctx.lineWidth = 2;
                ctx.lineCap = 'round';
                ctx.beginPath();
                ctx.moveTo(tailX, tailY);
                ctx.lineTo(x, y); 
                ctx.stroke();

                // Draw Head Glow
                ctx.fillStyle = '#fff';
                ctx.shadowBlur = 8;
                ctx.shadowColor = b.color;
                ctx.beginPath();
                ctx.arc(x, y, 2, 0, Math.PI * 2);
                ctx.fill();
                ctx.shadowBlur = 0;
            }

            animationFrameId = requestAnimationFrame(tick);
        };

        tick();
        return () => cancelAnimationFrame(animationFrameId);
    }, []); // Run once

    const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (canvas.width / rect.width); // Adjust for scaling if any
        const y = (e.clientY - rect.top) * (canvas.height / rect.height);

        // Use stable ref for mouse move to prevent stale closure issues if graphData updates
        const { nodes } = graphDataRef.current;
        let found: Node | null = null;
        
        // Use reverse loop to check top-most nodes first
        for (let i = nodes.length - 1; i >= 0; i--) {
            const node = nodes[i];
            const dist = Math.hypot(node.x - x, node.y - y);
            if (dist < 10) { // Hit radius
                found = node;
                break;
            }
        }
        
        setHoveredNode(found);
    };

    return (
        <div ref={containerRef} className="relative w-full h-full min-h-[600px] bg-[#020617] rounded-3xl overflow-hidden border border-white/10 shadow-2xl group">
            {/* World Map aligned with graph coordinate system */}
            <div className="absolute inset-0 z-0">
                <WorldMap width={dimensions.width} height={dimensions.height} />
            </div>
            
            {/* Background Grid/Map Texture could go here */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent pointer-events-none"></div>
            
            <canvas 
                ref={canvasRef} 
                className="w-full h-full block cursor-crosshair"
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setHoveredNode(null)}
            />
            
            {/* Tooltip Overlay */}
            {hoveredNode && (
                <div 
                    className="absolute z-50 pointer-events-none transform -translate-x-1/2 -translate-y-full mb-4"
                    style={{ left: hoveredNode.targetX / (canvasRef.current?.width || 1) * 100 + '%', top: hoveredNode.targetY / (canvasRef.current?.height || 1) * 100 + '%' }}
                >
                    <div className="bg-black/80 backdrop-blur-md border border-white/10 rounded-xl p-4 shadow-[0_0_30px_rgba(0,0,0,0.5)] min-w-[280px]">
                        <div className="flex items-center gap-3 mb-3 border-b border-white/10 pb-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${hoveredNode.color === '#ef4444' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                <div className="w-2 h-2 rounded-full bg-current animate-pulse"></div>
                            </div>
                            <div>
                                <h4 className="font-bold text-white text-sm">{hoveredNode.name}</h4>
                                <p className="text-[10px] font-mono text-muted-foreground">{hoveredNode.id.substring(0, 16)}...</p>
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-2 text-center">
                            <div className="bg-white/5 rounded-lg p-2">
                                <div className="text-[10px] text-muted-foreground uppercase mb-1">Invocations</div>
                                <div className="text-sm font-mono font-bold text-blue-400">
                                    {(hoveredNode.id.charCodeAt(0) * 123 + hoveredNode.id.charCodeAt(1) * 45).toLocaleString()}
                                </div>
                            </div>
                            <div className="bg-white/5 rounded-lg p-2">
                                <div className="text-[10px] text-muted-foreground uppercase mb-1">Latency</div>
                                <div className="text-sm font-mono font-bold text-green-400">
                                    {20 + (hoveredNode.id.charCodeAt(2) % 150)}ms
                                </div>
                            </div>
                            <div className="bg-white/5 rounded-lg p-2">
                                <div className="text-[10px] text-muted-foreground uppercase mb-1">Uptime</div>
                                <div className="text-sm font-mono font-bold text-purple-400">99.9%</div>
                            </div>
                        </div>

                        <div className="mt-3 pt-2 border-t border-white/5 flex justify-between items-center">
                            <span className="text-[10px] text-muted-foreground">Region: <span className="text-white">{hoveredNode.region}</span></span>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full ${hoveredNode.color === '#ef4444' ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
                                {hoveredNode.color === '#ef4444' ? 'Offline' : 'Active'}
                            </span>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Header */}
            <div className="absolute top-6 left-8 pointer-events-none">
                <div className="flex items-center gap-3 mb-1">
                    <div className="relative">
                        <span className="absolute inline-flex h-3 w-3 animate-ping rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex h-3 w-3 rounded-full bg-green-500"></span>
                    </div>
                    <h3 className="text-xl font-bold tracking-tight text-white">Global Mesh Topology</h3>
                </div>
                <div className="flex gap-4 text-xs font-mono text-blue-200/60">
                    <span>NODES: {agents.length}</span>
                    <span>LINKS: {graphData.links.length}</span>
                    <span>REGIONS: {Object.keys(REGIONS).length}</span>
                </div>
            </div>
        </div>
    );
}
