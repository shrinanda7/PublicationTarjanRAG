import React, { useEffect, useRef, useState, useMemo } from "react";
import cytoscape, { Core, EventObject } from "cytoscape";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Play,
  Pause,
  RotateCcw,
  Network,
  Info,
  X,
  Layers,
  Tag,
  Share2,
  Sparkles,
  Link2,
} from "lucide-react";
import { GraphTopology, TraversalStep, TraversalTrace, GraphNode } from "../types";

interface CytoscapeGraphViewerProps {
  originalGraph: GraphTopology | null;
  compressedGraph: GraphTopology | null;
  trace: TraversalTrace | null;
  selectedPaperTitles: string[];
  theme: "dark" | "light";
}

const PAPER_PALETTES = [
  { fillDark: "#6366f1", fillLight: "#4f46e5", strokeDark: "#a5b4fc", strokeLight: "#312e81", name: "Indigo" },
  { fillDark: "#06b6d4", fillLight: "#0891b2", strokeDark: "#67e8f9", strokeLight: "#164e63", name: "Cyan" },
  { fillDark: "#f59e0b", fillLight: "#d97706", strokeDark: "#fcd34d", strokeLight: "#78350f", name: "Amber" },
  { fillDark: "#10b981", fillLight: "#059669", strokeDark: "#6ee7b7", strokeLight: "#064e3b", name: "Emerald" },
  { fillDark: "#ec4899", fillLight: "#db2777", strokeDark: "#f472b6", strokeLight: "#831843", name: "Pink" },
  { fillDark: "#8b5cf6", fillLight: "#7c3aed", strokeDark: "#c4b5fd", strokeLight: "#4c1d95", name: "Purple" },
  { fillDark: "#f97316", fillLight: "#ea580c", strokeDark: "#fdba74", strokeLight: "#7c2d12", name: "Orange" },
];

export const CytoscapeGraphViewer: React.FC<CytoscapeGraphViewerProps> = ({
  originalGraph,
  compressedGraph,
  trace,
  selectedPaperTitles,
  theme,
}) => {
  const isDark = theme === "dark";
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  const [graphMode, setGraphMode] = useState<"compressed" | "original">("compressed");
  const [showEdgeLabels, setShowEdgeLabels] = useState<boolean>(true);
  const [focusCrossPaperOnly, setFocusCrossPaperOnly] = useState<boolean>(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(-1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [selectedNodeData, setSelectedNodeData] = useState<any>(null);

  const activeGraph = graphMode === "compressed" ? compressedGraph : originalGraph;
  const steps: TraversalStep[] = trace?.steps || [];

  // Detect distinct papers present in the active graph
  const paperMapping = useMemo(() => {
    if (!activeGraph?.nodes) return new Map<string, number>();
    const mapping = new Map<string, number>();
    let counter = 0;
    activeGraph.nodes.forEach((n) => {
      const pid = n.paper_id || (n.id.includes("::") ? n.id.split("::")[0] : "primary");
      if (!mapping.has(pid)) {
        mapping.set(pid, counter++);
      }
    });
    return mapping;
  }, [activeGraph]);

  const distinctPapersCount = paperMapping.size;

  // Count cross-paper bridges in the active graph
  const crossPaperBridgesCount = useMemo(() => {
    if (!activeGraph?.edges) return 0;
    return activeGraph.edges.filter((e) => {
      if (e.is_cross_paper) return true;
      if (e.source.includes("::") && e.target.includes("::")) {
        return e.source.split("::")[0] !== e.target.split("::")[0];
      }
      return false;
    }).length;
  }, [activeGraph]);

  // Initialize or update Cytoscape instance
  useEffect(() => {
    if (!containerRef.current) return;

    if (!activeGraph || !activeGraph.nodes || activeGraph.nodes.length === 0) {
      if (cyRef.current) {
        try {
          if (!cyRef.current.destroyed()) {
            cyRef.current.stop();
            cyRef.current.destroy();
          }
        } catch (e) {}
        cyRef.current = null;
      }
      setSelectedNodeData(null);
      return;
    }

    const articulationPoints = new Set(compressedGraph?.articulation_points || []);
    const bridgeEdgeKeys = new Set(
      (compressedGraph?.bridges || []).map(([u, v]) => `${u}->${v}`)
    );

    const elements: any[] = [];
    const nodeIds = new Set<string>();

    // Add nodes with paper-specific coloring
    activeGraph.nodes.forEach((n) => {
      if (!n?.id || nodeIds.has(n.id)) return;
      nodeIds.add(n.id);

      const pid = n.paper_id || (n.id.includes("::") ? n.id.split("::")[0] : "primary");
      const paperIdx = paperMapping.get(pid) || 0;
      const palette = PAPER_PALETTES[paperIdx % PAPER_PALETTES.length];

      const isAP = articulationPoints.has(n.id) || n.is_connector;
      const isSuper = n.is_supernode;
      const memberCount = n.member_count || (n.member_node_ids?.length || 1);

      // Multi-paper palette gives each paper a distinct color identity
      let color = isDark ? palette.fillDark : palette.fillLight;
      let borderColor = isDark ? palette.strokeDark : palette.strokeLight;

      if (isSuper) {
        color = isDark ? "#a79cff" : "#7164e8";
        borderColor = isDark ? "#c1baff" : "#4c1d95";
      } else if (isAP) {
        // Articulation connectors get cyan halo border
        borderColor = isDark ? "#22d3ee" : "#0891b2";
      }

      elements.push({
        data: {
          id: n.id,
          label: n.name,
          type: n.type,
          paperId: pid,
          description: n.description || "",
          isSupernode: isSuper,
          isConnector: isAP,
          memberCount: memberCount,
          memberNodes: n.member_nodes || [],
          originalColor: color,
          borderColor: borderColor,
        },
      });
    });

    // Add edges with cross-paper distinction
    activeGraph.edges.forEach((e, idx) => {
      if (!e?.source || !e?.target) return;
      if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) return;

      const isCrossPaper =
        Boolean(e.is_cross_paper) ||
        (e.source.includes("::") &&
          e.target.includes("::") &&
          e.source.split("::")[0] !== e.target.split("::")[0]);

      const isBridge =
        isCrossPaper ||
        e.is_bridge ||
        bridgeEdgeKeys.has(`${e.source}->${e.target}`) ||
        bridgeEdgeKeys.has(`${e.target}->${e.source}`);

      const displayLabel = isCrossPaper
        ? `🔗 ${e.type || "CROSS_PAPER_BRIDGE"}`
        : (e.type || "");

      elements.push({
        data: {
          id: `edge_${e.source}_${e.target}_${idx}`,
          source: e.source,
          target: e.target,
          label: displayLabel,
          type: e.type,
          isBridge: isBridge,
          isCrossPaper: isCrossPaper,
          weight: e.weight || (isCrossPaper ? 2.0 : 1.0),
        },
      });
    });

    try {
      const cy = cytoscape({
        container: containerRef.current,
        elements: elements,
        boxSelectionEnabled: false,
        autounselectify: false,
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              "font-size": "10px",
              "font-family": "ui-sans-serif, system-ui, sans-serif",
              color: isDark ? "#f8fafc" : "#0f172a",
              "text-valign": "bottom",
              "text-halign": "center",
              "text-margin-y": 4,
              "text-wrap": "wrap",
              "text-max-width": "110px",
              "background-color": "data(originalColor)",
              width: "mapData(memberCount, 1, 10, 26, 46)",
              height: "mapData(memberCount, 1, 10, 26, 46)",
              "border-width": 2,
              "border-color": "data(borderColor)",
              "border-opacity": 0.95,
              "transition-property": "background-color, border-color, border-width, width, height, opacity",
              "transition-duration": 250,
            },
          },
          {
            selector: "node[?isSupernode]",
            style: {
              shape: "hexagon",
              "border-width": 2.5,
              "border-color": isDark ? "#c1baff" : "#6255d9",
            },
          },
          {
            selector: "node[?isConnector]",
            style: {
              shape: "round-rectangle",
              "border-width": 3,
              "border-color": isDark ? "#22d3ee" : "#0891b2",
            },
          },
          // Standard intra-paper edge
          {
            selector: "edge",
            style: {
              label: showEdgeLabels ? "data(label)" : "",
              "font-size": "8px",
              "font-family": "ui-sans-serif, system-ui, sans-serif",
              "font-weight": 600,
              color: isDark ? "#94a3b8" : "#475569",
              "text-rotation": "autorotate",
              "text-margin-y": -6,
              "text-background-opacity": showEdgeLabels ? 0.85 : 0,
              "text-background-color": isDark ? "#0f172a" : "#f8fafc",
              "text-background-padding": "2px",
              "text-background-shape": "roundrectangle",
              "text-border-width": 0.5,
              "text-border-color": isDark ? "#334155" : "#cbd5e1",
              "text-border-opacity": 0.8,
              width: 1.5,
              "line-color": isDark ? "#334155" : "#cbd5e1",
              "target-arrow-color": isDark ? "#475569" : "#94a3b8",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              "arrow-scale": 0.8,
              opacity: 0.85,
              "transition-property": "line-color, target-arrow-color, width, opacity",
              "transition-duration": 250,
            },
          },
          // Intra-paper Tarjan bridge edge
          {
            selector: "edge[?isBridge][!isCrossPaper]",
            style: {
              width: 2.5,
              "line-color": isDark ? "#51c7b5" : "#168c7b",
              "target-arrow-color": isDark ? "#51c7b5" : "#168c7b",
              color: isDark ? "#9ae5d8" : "#126e62",
              "text-border-color": isDark ? "#168c7b" : "#51c7b5",
              "line-style": "solid",
              opacity: 1,
            },
          },
          // Prominent Cross-Paper Bridge Edge (Dashed radiant cyan / amber)
          {
            selector: "edge[?isCrossPaper]",
            style: {
              width: 3.5,
              "line-color": isDark ? "#22d3ee" : "#0284c7",
              "target-arrow-color": isDark ? "#22d3ee" : "#0284c7",
              color: isDark ? "#a5f3fc" : "#0369a1",
              "text-background-color": isDark ? "#083344" : "#ecfeff",
              "text-background-opacity": 0.95,
              "text-border-color": isDark ? "#22d3ee" : "#0284c7",
              "text-border-width": 1.2,
              "text-border-opacity": 0.9,
              "font-weight": 700,
              "font-size": "9px",
              "line-style": "dashed",
              "line-dash-pattern": [6, 4],
              "curve-style": "unbundled-bezier",
              "target-arrow-shape": "triangle",
              "arrow-scale": 1.2,
              opacity: 1,
              "z-index": 995,
            },
          },
          {
            selector: "node.highlighted",
            style: {
              "background-color": "#f59e0b",
              "border-color": "#ffffff",
              "border-width": 3.5,
              width: 38,
              height: 38,
              "z-index": 999,
            },
          },
          {
            selector: "edge.highlighted",
            style: {
              width: 4,
              "line-color": "#f59e0b",
              "target-arrow-color": "#f59e0b",
              color: "#f59e0b",
              "text-border-color": "#f59e0b",
              "text-background-color": isDark ? "#1e293b" : "#fef3c7",
              opacity: 1,
              "z-index": 998,
            },
          },
          {
            selector: "node.cross_paper_highlighted",
            style: {
              "border-color": isDark ? "#22d3ee" : "#0891b2",
              "border-width": 4,
              "border-opacity": 1.0,
              "z-index": 997,
            },
          },
          {
            selector: "edge.cross_paper_highlighted",
            style: {
              width: 4.5,
              "line-color": isDark ? "#22d3ee" : "#0284c7",
              "target-arrow-color": isDark ? "#22d3ee" : "#0284c7",
              opacity: 1,
              "z-index": 998,
            },
          },
          {
            selector: "node.dimmed",
            style: {
              opacity: 0.22,
            },
          },
          {
            selector: "edge.dimmed",
            style: {
              opacity: 0.12,
            },
          },
        ],
        layout: {
          name: "cose",
          animate: false,
          idealEdgeLength: distinctPapersCount > 1 ? 110 : 85,
          nodeOverlap: 25,
          refresh: 20,
          fit: true,
          padding: 35,
          randomize: false,
          componentSpacing: distinctPapersCount > 1 ? 130 : 100,
          nodeRepulsion: 450000,
          edgeElasticity: 100,
          nestingFactor: 5,
        } as any,
      });

      cy.on("tap", "node", (evt: EventObject) => {
        const node = evt.target;
        setSelectedNodeData(node.data());
      });

      cy.on("tap", (evt: EventObject) => {
        if (evt.target === cy) {
          setSelectedNodeData(null);
          cy.elements().removeClass("dimmed highlighted cross_paper_highlighted");
          setFocusCrossPaperOnly(false);
        }
      });

      cyRef.current = cy;
    } catch (e) {
      console.error("Cytoscape init error:", e);
    }

    return () => {
      if (cyRef.current) {
        try {
          if (!cyRef.current.destroyed()) {
            cyRef.current.stop();
            cyRef.current.destroy();
          }
        } catch (e) {}
        cyRef.current = null;
      }
    };
  }, [activeGraph, graphMode, theme, showEdgeLabels, distinctPapersCount]);

  // Toggle focus on cross-paper bridge connections
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;

    if (focusCrossPaperOnly) {
      const crossEdges = cy.edges("[?isCrossPaper]");
      if (crossEdges.length > 0) {
        cy.elements().addClass("dimmed").removeClass("cross_paper_highlighted highlighted");
        crossEdges.removeClass("dimmed").addClass("cross_paper_highlighted");
        crossEdges.connectedNodes().removeClass("dimmed").addClass("cross_paper_highlighted");
      }
    } else if (currentStepIndex === -1) {
      cy.elements().removeClass("dimmed highlighted cross_paper_highlighted");
    }
  }, [focusCrossPaperOnly, currentStepIndex]);

  // Handle trace animation steps
  useEffect(() => {
    if (!cyRef.current || currentStepIndex < 0 || currentStepIndex >= steps.length) {
      if (currentStepIndex === -1 && cyRef.current && !focusCrossPaperOnly) {
        cyRef.current.elements().removeClass("highlighted dimmed cross_paper_highlighted");
      }
      return;
    }

    const cy = cyRef.current;
    const step = steps[currentStepIndex];

    cy.elements().addClass("dimmed").removeClass("highlighted cross_paper_highlighted");

    const targetNode = cy.getElementById(step.node_or_comm_id);
    if (targetNode && targetNode.length) {
      targetNode.removeClass("dimmed").addClass("highlighted");

      if (step.action === "EXPAND" || step.action === "BRIDGE_PRESERVE") {
        const connectedEdges = targetNode.connectedEdges();
        connectedEdges.removeClass("dimmed").addClass("highlighted");
        connectedEdges.connectedNodes().removeClass("dimmed");
      }

      cy.animate(
        {
          center: { eles: targetNode },
          zoom: Math.max(cy.zoom(), 1.1),
        },
        { duration: 300 }
      );
    }
  }, [currentStepIndex, steps, focusCrossPaperOnly]);

  // Auto-play trace animation
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying) {
      if (currentStepIndex < steps.length - 1) {
        timer = setTimeout(() => {
          setCurrentStepIndex((prev) => prev + 1);
        }, 1100);
      } else {
        setIsPlaying(false);
      }
    }
    return () => clearTimeout(timer);
  }, [isPlaying, currentStepIndex, steps.length]);

  return (
    <div
      className={`flex-1 h-full flex flex-col relative overflow-hidden transition-colors duration-200 select-none ${
        isDark ? "bg-slate-950" : "bg-slate-100/60"
      }`}
    >
      {/* Top Toolbar */}
      <div
        className={`px-4 py-2.5 border-b flex flex-wrap items-center justify-between gap-3 z-10 transition-colors ${
          isDark
            ? "bg-slate-950/90 border-slate-800/80 text-white backdrop-blur-md"
            : "bg-white/95 border-slate-200 text-slate-900 shadow-2xs backdrop-blur-md"
        }`}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <Network className="w-4 h-4 text-indigo-500" />
          <span className="text-xs font-semibold tracking-tight">
            {selectedPaperTitles.length === 0
              ? "Global Knowledge Graph"
              : selectedPaperTitles.length === 1
              ? selectedPaperTitles[0]
              : `Multi-Paper Graph (${selectedPaperTitles.length} papers)`}
          </span>
          <span className="text-xs text-slate-400">·</span>
          <span className="text-xs text-slate-500">
            {activeGraph?.nodes.length || 0} nodes · {activeGraph?.edges.length || 0} relations
          </span>

          {/* Cross-Paper Connection Badge */}
          {crossPaperBridgesCount > 0 && (
            <button
              onClick={() => setFocusCrossPaperOnly(!focusCrossPaperOnly)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border transition-all cursor-pointer ${
                focusCrossPaperOnly
                  ? isDark
                    ? "bg-cyan-500/25 border-cyan-400 text-cyan-200 shadow-xs shadow-cyan-500/20"
                    : "bg-cyan-100 border-cyan-500 text-cyan-800 shadow-xs"
                  : isDark
                  ? "bg-cyan-950/60 border-cyan-800/80 text-cyan-300 hover:border-cyan-500"
                  : "bg-cyan-50 border-cyan-200 text-cyan-700 hover:border-cyan-400"
              }`}
              title="Click to highlight/isolate cross-paper bridge edges"
            >
              <Link2 className="w-3 h-3 text-cyan-400 animate-pulse" />
              <span>{crossPaperBridgesCount} Cross-Paper Bridges</span>
              <span className={`text-[10px] px-1 py-0.2 rounded font-mono ${
                focusCrossPaperOnly
                  ? isDark ? "bg-cyan-400/20 text-cyan-200" : "bg-cyan-200 text-cyan-900"
                  : isDark ? "bg-slate-800 text-slate-400" : "bg-slate-200 text-slate-600"
              }`}>
                {focusCrossPaperOnly ? "Active" : "Focus"}
              </span>
            </button>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {/* Segmented Graph View Switcher */}
          <div
            className={`flex items-center p-0.5 rounded-lg border ${
              isDark
                ? "bg-slate-900 border-slate-800"
                : "bg-slate-100 border-slate-200"
            }`}
          >
            <button
              onClick={() => setGraphMode("compressed")}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                graphMode === "compressed"
                  ? isDark
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "bg-white text-slate-900 shadow-2xs"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Tarjan SCC Quotient
            </button>
            <button
              onClick={() => setGraphMode("original")}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                graphMode === "original"
                  ? isDark
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "bg-white text-slate-900 shadow-2xs"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Full Graph
            </button>
          </div>

          {/* Trace Playback if steps exist */}
          {steps.length > 0 && (
            <div
              className={`flex items-center gap-1 px-1.5 py-0.5 rounded-lg border ${
                isDark ? "bg-slate-900 border-slate-800" : "bg-slate-100 border-slate-200"
              }`}
            >
              <button
                onClick={() => {
                  if (currentStepIndex >= steps.length - 1) setCurrentStepIndex(0);
                  setIsPlaying(!isPlaying);
                }}
                className={`p-1 rounded hover:bg-slate-800 text-xs ${
                  isPlaying ? "text-amber-400" : "text-slate-400"
                }`}
                title={isPlaying ? "Pause Trace" : "Play Traversal"}
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentStepIndex(-1);
                }}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 text-xs"
                title="Reset Traversal"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Zoom & Fit */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.25)}
              className={`p-1.5 rounded-lg border transition-colors ${
                isDark
                  ? "bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-400"
                  : "bg-white hover:bg-slate-100 border-slate-200 text-slate-700 shadow-2xs"
              }`}
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
              className={`p-1.5 rounded-lg border transition-colors ${
                isDark
                  ? "bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-400"
                  : "bg-white hover:bg-slate-100 border-slate-200 text-slate-700 shadow-2xs"
              }`}
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setShowEdgeLabels(!showEdgeLabels)}
              className={`p-1.5 rounded-lg border transition-colors flex items-center gap-1 ${
                showEdgeLabels
                  ? isDark
                    ? "bg-indigo-600/30 border-indigo-500/50 text-indigo-300"
                    : "bg-indigo-50 border-indigo-200 text-indigo-700"
                  : isDark
                  ? "bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-400"
                  : "bg-white hover:bg-slate-100 border-slate-200 text-slate-700 shadow-2xs"
              }`}
              title={showEdgeLabels ? "Hide Edge Labels" : "Show Edge Labels"}
            >
              <Tag className="w-3.5 h-3.5" />
              <span className="text-[10px] font-medium hidden sm:inline">Labels</span>
            </button>
            <button
              onClick={() => cyRef.current?.fit(undefined, 30)}
              className={`p-1.5 rounded-lg border transition-colors ${
                isDark
                  ? "bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-400"
                  : "bg-white hover:bg-slate-100 border-slate-200 text-slate-700 shadow-2xs"
              }`}
              title="Fit to Screen"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Cytoscape Canvas Container */}
      <div ref={containerRef} className="flex-1 w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Multi-Paper Color Legend Bar (when multiple papers selected) */}
      {distinctPapersCount > 1 && (
        <div
          className={`absolute bottom-3 left-4 p-2.5 rounded-xl border shadow-lg z-20 text-[11px] backdrop-blur-md flex flex-wrap items-center gap-3 max-w-2xl transition-colors ${
            isDark
              ? "bg-slate-900/90 border-slate-800 text-slate-300"
              : "bg-white/90 border-slate-200 text-slate-700 shadow-sm"
          }`}
        >
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1">
            <Layers className="w-3 h-3 text-indigo-400" />
            Corpus Clusters:
          </span>
          <div className="flex flex-wrap items-center gap-2">
            {Array.from(paperMapping.entries()).map(([pid, idx]) => {
              const palette = PAPER_PALETTES[idx % PAPER_PALETTES.length];
              const titleCandidate =
                selectedPaperTitles[idx] ||
                pid.replace(/^[0-9._]+/, "").replace(/_/g, " ").slice(0, 24);
              return (
                <div key={pid} className="flex items-center gap-1.5 bg-slate-800/40 px-2 py-0.5 rounded-md border border-slate-700/40">
                  <span
                    className="w-2.5 h-2.5 rounded-full inline-block"
                    style={{ backgroundColor: isDark ? palette.fillDark : palette.fillLight }}
                  />
                  <span className="truncate max-w-[140px] text-xs font-medium">
                    {titleCandidate}
                  </span>
                </div>
              );
            })}

            {/* Cross-Paper Bridge Legend */}
            <div className="flex items-center gap-1.5 bg-cyan-950/40 px-2 py-0.5 rounded-md border border-cyan-800/60 text-cyan-300">
              <span className="font-mono text-cyan-400 font-bold">--- 🔗</span>
              <span className="text-xs font-medium">Cross-Paper Bridge</span>
            </div>
          </div>
        </div>
      )}

      {/* Empty State when no paper graph selected or all papers deleted */}
      {(!activeGraph || !activeGraph.nodes || activeGraph.nodes.length === 0) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center z-10 pointer-events-none">
          <div
            className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-3 border ${
              isDark
                ? "bg-slate-900/90 border-slate-800 text-slate-500"
                : "bg-slate-100/90 border-slate-200 text-slate-400"
            }`}
          >
            <Network className="w-7 h-7" />
          </div>
          <h3 className={`text-sm font-semibold mb-1 ${isDark ? "text-slate-300" : "text-slate-700"}`}>
            No Paper Graph Selected
          </h3>
          <p className="text-xs text-slate-500 max-w-xs leading-relaxed">
            Upload a research paper or select multiple papers from the sidebar to visualize knowledge graphs and cross-paper bridge connections.
          </p>
        </div>
      )}

      {/* Traversal Step Overlay if active */}
      {currentStepIndex >= 0 && steps[currentStepIndex] && (
        <div
          className={`absolute bottom-16 left-5 max-w-md p-3.5 rounded-xl border shadow-lg z-20 text-xs transition-colors ${
            isDark
              ? "bg-slate-900/95 border-amber-500/40 text-slate-200 backdrop-blur-md"
              : "bg-white/95 border-amber-500/40 text-slate-800 shadow-md backdrop-blur-md"
          }`}
        >
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-amber-500 font-mono">
                Step {currentStepIndex + 1}/{steps.length}
              </span>
              <span className="text-slate-400">·</span>
              <span className="font-semibold text-white">
                {steps[currentStepIndex].action}
              </span>
            </div>
            <span className="font-mono text-[11px] text-slate-400">
              Score: {steps[currentStepIndex].score}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            {steps[currentStepIndex].reason}
          </p>
        </div>
      )}

      {/* Node Inspector Drawer */}
      {selectedNodeData && (
        <div
          className={`absolute top-14 right-5 w-84 p-4 rounded-xl border shadow-xl z-20 text-xs transition-colors ${
            isDark
              ? "bg-slate-900/95 border-slate-800 text-slate-200 backdrop-blur-md"
              : "bg-white/95 border-slate-200 text-slate-800 shadow-md backdrop-blur-md"
          }`}
        >
          <div className="flex items-start justify-between gap-2 border-b pb-2.5 mb-2.5 border-slate-800/60">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] uppercase font-semibold text-indigo-400 tracking-wider">
                  {selectedNodeData.type}
                </span>
                {selectedNodeData.paperId && (
                  <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.2 rounded font-mono truncate max-w-[120px]">
                    {selectedNodeData.paperId.replace(/^[0-9._]+/, "")}
                  </span>
                )}
              </div>
              <h3 className="text-sm font-semibold text-white leading-snug">
                {selectedNodeData.label}
              </h3>
            </div>
            <button
              onClick={() => setSelectedNodeData(null)}
              className="text-slate-400 hover:text-white p-1 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
            {selectedNodeData.description || "Topological knowledge node extracted from academic literature."}
          </p>

          <div className="space-y-1.5 text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
            <div className="flex justify-between">
              <span>Node ID:</span>
              <span className="font-mono text-slate-300 truncate max-w-[160px]">{selectedNodeData.id}</span>
            </div>
            {selectedNodeData.isSupernode && (
              <div className="flex justify-between">
                <span>Condensed Members:</span>
                <span className="text-purple-400 font-semibold">
                  {selectedNodeData.memberCount} nodes
                </span>
              </div>
            )}
            {selectedNodeData.isConnector && (
              <div className="flex justify-between">
                <span>Structure:</span>
                <span className="text-cyan-400 font-medium flex items-center gap-1">
                  <Link2 className="w-3 h-3" /> Cross-Paper Articulation Bridge
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
