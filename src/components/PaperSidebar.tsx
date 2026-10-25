import React, { useState, useRef, useEffect } from "react";
import {
  Upload, Search, CheckSquare, Square, FileText, Check, Plus, Loader2,
  Trash2, Folder, FolderPlus, Sparkles, Tag, ChevronDown, X, Link2, GraduationCap
} from "lucide-react";
import { Paper } from "../types";

interface PaperSidebarProps {
  papers: Paper[];
  selectedPaperIds: string[];
  onTogglePaper: (paperId: string) => void;
  onSelectOnlyPaper: (paperId: string) => void;
  onSelectAll: () => void;
  onClearSelection: () => void;
  onDeletePaper: (paperId: string) => void;
  onPapersUploaded: (newPaperId?: string) => void;
  onIndexSelected: (paperIds: string[], onProgress: (message: string) => void) => Promise<string | void>;
  showResearchIndexButton: boolean;
  onSummarizePaper?: (paper: Paper) => void;
  theme: "dark" | "light";
}

const DEFAULT_FOLDERS = [
  "All Sources",
  "Transformers & Attention",
  "Graph Neural Networks",
  "RAG & Multi-Hop",
  "Custom Uploads",
];

export const PaperSidebar: React.FC<PaperSidebarProps> = ({
  papers,
  selectedPaperIds,
  onTogglePaper,
  onSelectOnlyPaper,
  onSelectAll,
  onClearSelection,
  onDeletePaper,
  onPapersUploaded,
  onIndexSelected,
  showResearchIndexButton,
  onSummarizePaper,
  theme,
}) => {
  const isDark = theme === "dark";
  const [searchQuery, setSearchQuery] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [isIndexingResearch, setIsIndexingResearch] = useState(false);
  const [researchIndexMessage, setResearchIndexMessage] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Folder states
  const [folders, setFolders] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem("graphrag_folders");
      return saved ? JSON.parse(saved) : DEFAULT_FOLDERS;
    } catch {
      return DEFAULT_FOLDERS;
    }
  });

  const [activeFolder, setActiveFolder] = useState<string>("All Sources");
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [isImportingUrl, setIsImportingUrl] = useState(false);
  const [urlImportValue, setUrlImportValue] = useState("");
  const [urlImportError, setUrlImportError] = useState<string | null>(null);
  const [isImportingArxiv, setIsImportingArxiv] = useState(false);
  const [isArxivPanelOpen, setIsArxivPanelOpen] = useState(false);
  const [arxivTopic, setArxivTopic] = useState("");
  const [arxivCount, setArxivCount] = useState(5);
  const [arxivMessage, setArxivMessage] = useState<string | null>(null);
  const [arxivError, setArxivError] = useState<string | null>(null);

  // Paper-to-folder mapping
  const [paperFolderMap, setPaperFolderMap] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem("graphrag_paper_folders");
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem("graphrag_folders", JSON.stringify(folders));
    } catch {}
  }, [folders]);

  useEffect(() => {
    try {
      localStorage.setItem("graphrag_paper_folders", JSON.stringify(paperFolderMap));
    } catch {}
  }, [paperFolderMap]);

  // Assign default categories to built-in papers if not set
  useEffect(() => {
    setPaperFolderMap((prev) => {
      const updated = { ...prev };
      let changed = false;
      papers.forEach((p) => {
        if (!updated[p.paper_id]) {
          const t = p.title.toLowerCase();
          if (t.includes("attention") || t.includes("bert")) {
            updated[p.paper_id] = "Transformers & Attention";
            changed = true;
          } else if (t.includes("gcn") || t.includes("gat") || t.includes("graphsage")) {
            updated[p.paper_id] = "Graph Neural Networks";
            changed = true;
          } else if (t.includes("rag") || t.includes("thought")) {
            updated[p.paper_id] = "RAG & Multi-Hop";
            changed = true;
          } else {
            updated[p.paper_id] = "Custom Uploads";
            changed = true;
          }
        }
      });
      return changed ? updated : prev;
    });
  }, [papers]);

  const handleCreateFolder = () => {
    const trimmed = newFolderName.trim();
    if (!trimmed) return;
    if (!folders.includes(trimmed)) {
      setFolders((prev) => [...prev, trimmed]);
      setActiveFolder(trimmed);
    }
    setNewFolderName("");
    setIsCreatingFolder(false);
  };

  const handleDeleteFolder = (folder: string) => {
    if (folder === "All Sources" || folder === "Custom Uploads") return;
    const count = papers.filter((paper) => (paperFolderMap[paper.paper_id] || "Custom Uploads") === folder).length;
    if (!window.confirm(`Delete the “${folder}” folder? ${count} paper(s) will be moved to Custom Uploads. The papers themselves will not be deleted.`)) return;
    setFolders((current) => current.filter((name) => name !== folder));
    setPaperFolderMap((current) => {
      const next = { ...current };
      for (const paper of papers) if ((next[paper.paper_id] || "Custom Uploads") === folder) next[paper.paper_id] = "Custom Uploads";
      return next;
    });
    if (activeFolder === folder) setActiveFolder("All Sources");
  };

  const handleIndexSelected = async () => {
    if (!selectedPaperIds.length || isIndexingResearch) return;
    setIsIndexingResearch(true);
    setResearchIndexMessage(`Starting research indexing for ${selectedPaperIds.length} paper(s)…`);
    try {
      const completionMessage = await onIndexSelected(selectedPaperIds, setResearchIndexMessage);
      setResearchIndexMessage(completionMessage || "Research chunks and graph data are ready for the selected papers.");
      window.setTimeout(() => setResearchIndexMessage(null), 6000);
    } catch (error: any) {
      setResearchIndexMessage(error?.message || "Research indexing failed.");
    } finally {
      setIsIndexingResearch(false);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const supported = Array.from(files).filter((file) => /\.(pdf|docx|pptx|txt|md|html?|png|jpe?g|tiff?|bmp)$/i.test(file.name));
    if (supported.length === 0) {
      alert("Choose PDF, DOCX, PPTX, TXT, Markdown, HTML, PNG, JPG, TIFF, or BMP files.");
      return;
    }

    const titles: string[] = [];
    for (const file of supported) {
      const defaultTitle = file.name.replace(/\.[^.]+$/, "").replace(/[_-]/g, " ").trim();
      const enteredTitle = window.prompt(
        `Enter a title for "${file.name}" (or leave blank to use the filename):`,
        defaultTitle
      );
      titles.push(enteredTitle && enteredTitle.trim() ? enteredTitle.trim() : defaultTitle);
    }

    setIsUploading(true);
    setUploadMessage(`Extracting ${supported.length} document(s)...`);

    try {
      const formData = new FormData();
      supported.forEach((file, index) => {
        formData.append("files", file);
        formData.append("custom_titles", titles[index]);
      });

      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "Failed to process upload");
      }

      const data = await res.json();
      const uploadedList = data.uploaded_papers || data.papers || (data.paper ? [data.paper] : []);

      // Tag uploaded papers with the current folder
      if (uploadedList.length > 0) {
        setPaperFolderMap((prev) => {
          const next = { ...prev };
          const target = activeFolder === "All Sources" ? "Custom Uploads" : activeFolder;
          uploadedList.forEach((up: any) => {
            if (up.paper_id) next[up.paper_id] = target;
          });
          return next;
        });
      }

      setUploadMessage(`Imported ${uploadedList.length} source(s) successfully!`);
      setTimeout(() => {
        setIsUploading(false);
        setUploadMessage(null);
        const newestId = uploadedList[0]?.paper_id;
        onPapersUploaded(newestId);
      }, 700);
    } catch (err: any) {
      alert(err.message || "Upload failed");
      setIsUploading(false);
      setUploadMessage(null);
    }
  };

  const handleImportUrl = async () => {
    const url = urlImportValue.trim();
    if (!url) {
      setUrlImportError("Enter a webpage URL to import.");
      return;
    }
    if (!/^https?:\/\//i.test(url)) {
      setUrlImportError("Use a full webpage address starting with https:// or http://.");
      return;
    }
    setIsUploading(true);
    setUrlImportError(null);
    setUploadMessage("Fetching webpage and extracting readable text…");
    try {
      const response = await fetch("/api/import-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || "Webpage import failed.");
      const imported = payload.paper || payload.papers?.[0];
      if (imported?.paper_id) {
        setPaperFolderMap((current) => ({ ...current, [imported.paper_id]: activeFolder === "All Sources" ? "Custom Uploads" : activeFolder }));
      }
      setIsUploading(false);
      setUploadMessage(null);
      setIsImportingUrl(false);
      setUrlImportValue("");
      onPapersUploaded(imported?.paper_id);
    } catch (error: any) {
      setIsUploading(false);
      setUploadMessage(null);
      setUrlImportError(error?.message || "Webpage import failed.");
    }
  };

  const handleImportArxiv = async () => {
    const topic = arxivTopic.trim();
    if (topic.length < 2) {
      setArxivError("Enter a research topic to search arXiv.");
      return;
    }
    setIsImportingArxiv(true);
    setArxivError(null);
    setArxivMessage("Searching arXiv and importing matching papers…");
    try {
      const response = await fetch("/api/import-arxiv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, count: arxivCount }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || payload.message || `arXiv import request failed (HTTP ${response.status}). Restart the app server if this route was just added.`);
      const importedPapers = payload.imported || payload.papers || [];
      if (importedPapers.length) {
        const destination = activeFolder === "All Sources" ? "Custom Uploads" : activeFolder;
        setPaperFolderMap((current) => {
          const next = { ...current };
          importedPapers.forEach((paper: Paper) => { next[paper.paper_id] = destination; });
          return next;
        });
        setArxivMessage(`${payload.message || `Imported ${importedPapers.length} paper(s).`} Saved to ${destination}.`);
        setArxivTopic("");
        onPapersUploaded(importedPapers[0]?.paper_id);
      } else {
        const skipped = Array.isArray(payload.skipped) ? payload.skipped : [];
        if (skipped.length) throw new Error(`No papers were imported. ${skipped.slice(0, 3).join("; ")}${skipped.length > 3 ? `; and ${skipped.length - 3} more` : ""}`);
        setArxivMessage(payload.message || "No papers were imported.");
      }
    } catch (error: any) {
      setArxivError(error?.message || "arXiv import failed.");
      setArxivMessage(null);
    } finally {
      setIsImportingArxiv(false);
    }
  };

  // Filter papers by search query and active folder
  const filteredPapers = papers.filter((p) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      p.title.toLowerCase().includes(q) ||
      (p.filename && p.filename.toLowerCase().includes(q));

    if (!matchesSearch) return false;
    if (activeFolder === "All Sources") return true;

    const paperFolder = paperFolderMap[p.paper_id] || "Custom Uploads";
    return paperFolder === activeFolder;
  });

  const allSelected = papers.length > 0 && selectedPaperIds.length === papers.length;

  return (
    <aside
      className={`w-80 h-full border-r flex flex-col transition-colors duration-200 select-none ${
        isDark
          ? "bg-slate-950 border-slate-800/80 text-slate-200"
          : "bg-slate-50 border-slate-200 text-slate-800"
      }`}
    >
      {/* Sidebar Header */}
      <div
        className={`p-3 border-b flex flex-col gap-2 ${
          isDark ? "border-slate-800/80 bg-slate-900/40" : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Research Corpus
            </h2>
            <div className="text-xs text-slate-500 mt-0.5">
              <span>{selectedPaperIds.length} of {papers.length} active</span>
              <span className="mx-1.5">·</span>
              <span>Multi-select enabled</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={allSelected ? onClearSelection : onSelectAll}
              className={`px-2.5 py-1 text-xs font-medium rounded-md border transition-colors ${
                isDark
                  ? "bg-slate-900 hover:bg-slate-800 border-slate-700 text-slate-300"
                  : "bg-white hover:bg-slate-100 border-slate-300 text-slate-700 shadow-2xs"
              }`}
            >
              {allSelected ? "Clear" : "Select All"}
            </button>
          </div>
        </div>

        {showResearchIndexButton && <button
          type="button"
          onClick={handleIndexSelected}
          disabled={!selectedPaperIds.length || isIndexingResearch}
          className={`w-full rounded-lg px-3 py-2 text-xs font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-50 ${isDark ? "bg-indigo-600 hover:bg-indigo-500 text-white" : "bg-indigo-600 hover:bg-indigo-700 text-white"}`}
          title="Create source chunks and index selected papers in the Python research backend"
        >
          {isIndexingResearch ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          {isIndexingResearch ? "Indexing for research…" : `Index ${selectedPaperIds.length || "selected"} for research`}
        </button>}
        {showResearchIndexButton && researchIndexMessage && <div className="text-[11px] text-slate-400 leading-relaxed">{researchIndexMessage}</div>}

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search papers by title or topic..."
            className={`w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border outline-none transition-all ${
              isDark
                ? "bg-slate-900/80 border-slate-800 text-white placeholder-slate-500 focus:border-indigo-500"
                : "bg-slate-100/70 border-slate-200 text-slate-900 placeholder-slate-400 focus:border-indigo-600 focus:bg-white"
            }`}
          />
        </div>

        <details className={`group rounded-lg border ${isDark ? "border-slate-800 bg-slate-950/30" : "border-slate-200 bg-slate-50/70"}`}>
          <summary className={`flex cursor-pointer list-none items-center justify-between gap-2 rounded-lg px-3 py-2 text-xs font-semibold [&::-webkit-details-marker]:hidden ${isDark ? "text-slate-300 hover:bg-slate-900" : "text-slate-700 hover:bg-white"}`}>
            <span className="flex min-w-0 items-center gap-2"><Plus className="h-3.5 w-3.5 shrink-0 text-indigo-400" /> Add sources</span>
            <span className="text-[10px] font-normal text-slate-500">Upload · Web · arXiv</span>
          </summary>
          <div className="space-y-2 border-t border-slate-800/50 p-2">
        {/* Dropzone / Upload Action */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            handleFileUpload(e.dataTransfer.files);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`border border-dashed rounded-lg p-2.5 text-center cursor-pointer transition-all ${
            dragActive
              ? "border-indigo-500 bg-indigo-500/10"
              : isDark
              ? "border-slate-800 hover:border-slate-700 bg-slate-900/30 hover:bg-slate-900/50"
              : "border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-50 shadow-2xs"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.pptx,.txt,.md,.html,.htm,.png,.jpg,.jpeg,.tif,.tiff,.bmp"
            className="hidden"
            onChange={(e) => handleFileUpload(e.target.files)}
          />
          {isUploading ? (
            <div className="flex items-center justify-center gap-2 text-xs text-indigo-400 py-1">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{uploadMessage || "Indexing PDF text & graph..."}</span>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2 text-xs font-medium">
              <Upload className="w-3.5 h-3.5 text-indigo-400" />
              <span className={isDark ? "text-slate-300" : "text-slate-700"}>
                Upload documents or images to{" "}
                <strong className="text-indigo-400 font-semibold">
                  {activeFolder === "All Sources" ? "Corpus" : activeFolder}
                </strong>
              </span>
            </div>
          )}
        </div>

        {!isImportingUrl ? (
          <button type="button" onClick={() => { setIsImportingUrl(true); setUrlImportError(null); }} disabled={isUploading} className={`w-full mt-2 flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium transition-colors disabled:opacity-50 ${isDark ? "border-slate-700 bg-slate-900/60 text-slate-300 hover:border-indigo-500/60 hover:text-white" : "border-slate-200 bg-white text-slate-700 hover:border-indigo-300 hover:text-indigo-700"}`}>
            <Link2 className="w-3.5 h-3.5 text-teal-400" /> Import webpage URL
          </button>
        ) : (
          <form className="mt-2 space-y-1.5" onSubmit={(event) => { event.preventDefault(); void handleImportUrl(); }}>
            <label htmlFor="webpage-import-url" className="block px-1 text-[11px] font-medium text-slate-500">Webpage address</label>
            <div className="flex gap-1.5">
              <input id="webpage-import-url" type="url" value={urlImportValue} onChange={(event) => { setUrlImportValue(event.target.value); setUrlImportError(null); }} placeholder="https://example.com/article" disabled={isUploading} autoFocus className={`min-w-0 flex-1 rounded-lg border px-2 py-2 text-xs outline-none focus:border-teal-500 ${isDark ? "border-slate-700 bg-slate-900 text-white placeholder:text-slate-600" : "border-slate-300 bg-white text-slate-900 placeholder:text-slate-400"}`} />
              <button type="submit" disabled={isUploading || !urlImportValue.trim()} className="rounded-lg bg-teal-600 px-2.5 text-xs font-semibold text-white hover:bg-teal-500 disabled:opacity-50">{isUploading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Import"}</button>
              <button type="button" disabled={isUploading} onClick={() => { setIsImportingUrl(false); setUrlImportError(null); setUrlImportValue(""); }} className={`rounded-lg border px-2 text-xs ${isDark ? "border-slate-700 text-slate-400 hover:text-white" : "border-slate-300 text-slate-500 hover:text-slate-900"}`} aria-label="Cancel webpage import">Cancel</button>
            </div>
            {urlImportError && <p role="alert" className="px-1 text-[11px] leading-relaxed text-rose-400">{urlImportError}</p>}
          </form>
        )}
        {!isArxivPanelOpen ? (
          <button type="button" onClick={() => { setIsArxivPanelOpen(true); setArxivError(null); }} disabled={isUploading || isImportingArxiv} className={`w-full mt-1.5 flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium transition-colors disabled:opacity-50 ${isDark ? "border-slate-700 bg-slate-900/60 text-slate-300 hover:border-amber-500/60 hover:text-white" : "border-slate-200 bg-white text-slate-700 hover:border-amber-300 hover:text-amber-800"}`}>
            <GraduationCap className="h-3.5 w-3.5 text-amber-500" /> Find papers on arXiv
          </button>
        ) : (
          <form className={`mt-2 space-y-2 rounded-xl border p-3 ${isDark ? "border-slate-800 bg-slate-900/60" : "border-slate-200 bg-white"}`} onSubmit={(event) => { event.preventDefault(); void handleImportArxiv(); }}>
            <div className="flex items-center justify-between gap-2">
              <label htmlFor="arxiv-topic" className={`text-xs font-semibold ${isDark ? "text-slate-200" : "text-slate-800"}`}>Search arXiv papers</label>
              <button type="button" onClick={() => { setIsArxivPanelOpen(false); setArxivError(null); }} disabled={isImportingArxiv} className="rounded p-1 text-slate-500 hover:text-slate-200" aria-label="Close arXiv search"><X className="h-3.5 w-3.5" /></button>
            </div>
            <input id="arxiv-topic" type="text" value={arxivTopic} onChange={(event) => { setArxivTopic(event.target.value); setArxivError(null); }} maxLength={200} placeholder="e.g. graph neural networks for RAG" disabled={isImportingArxiv} className={`w-full rounded-lg border px-2.5 py-2 text-xs outline-none focus:border-amber-500 ${isDark ? "border-slate-700 bg-slate-950 text-white placeholder:text-slate-600" : "border-slate-300 bg-white text-slate-900 placeholder:text-slate-400"}`} />
            <div className="flex items-center justify-between gap-2">
              <label htmlFor="arxiv-count" className="text-[11px] text-slate-500">Number of papers (1–10)</label>
              <input id="arxiv-count" type="number" min={1} max={10} step={1} value={arxivCount} onChange={(event) => setArxivCount(Math.max(1, Math.min(10, Number(event.target.value) || 1)))} disabled={isImportingArxiv} className={`w-16 rounded-lg border px-2 py-1.5 text-center text-xs outline-none focus:border-amber-500 ${isDark ? "border-slate-700 bg-slate-950 text-white" : "border-slate-300 bg-white text-slate-900"}`} />
            </div>
            <p className="text-[10px] leading-relaxed text-slate-500">Imports are saved to <strong className="font-medium text-slate-400">{activeFolder === "All Sources" ? "Custom Uploads" : activeFolder}</strong>. Results are ranked by arXiv relevance.</p>
            <button type="submit" disabled={isImportingArxiv || !arxivTopic.trim()} className="flex w-full items-center justify-center gap-2 rounded-lg bg-amber-600 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-amber-500 disabled:opacity-50">
              {isImportingArxiv ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Importing papers…</> : <><GraduationCap className="h-3.5 w-3.5" /> Search and import papers</>}
            </button>
            {arxivMessage && <p role="status" className="text-[11px] leading-relaxed text-emerald-500">{arxivMessage}</p>}
            {arxivError && <p role="alert" className="text-[11px] leading-relaxed text-rose-400">{arxivError}</p>}
          </form>
        )}
        <p className="px-1 text-[10px] leading-relaxed text-slate-500">Scanned PDFs and images use free local Tesseract OCR. See OCR_SETUP.md if OCR is not installed.</p>
          </div>
        </details>

        {/* Folders Bar (Notebook style) */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1">
              <Folder className="w-3 h-3 text-amber-500" /> Folders / Categories
            </span>
            <button
              onClick={() => setIsCreatingFolder(!isCreatingFolder)}
              className="text-[10px] text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5 font-medium"
              title="Create new folder heading"
            >
              <Plus className="w-3 h-3" /> New
            </button>
          </div>

          {isCreatingFolder && (
            <div className="flex items-center gap-1.5 mb-2">
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()}
                placeholder="Folder name..."
                className={`flex-1 px-2 py-1 text-xs rounded border outline-none ${
                  isDark
                    ? "bg-slate-800 border-slate-700 text-white"
                    : "bg-white border-slate-300 text-slate-900"
                }`}
                autoFocus
              />
              <button
                onClick={handleCreateFolder}
                className="px-2 py-1 text-xs bg-indigo-600 hover:bg-indigo-500 text-white rounded font-medium"
              >
                Add
              </button>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-1 pb-1">
            {folders.map((f) => {
              const count =
                f === "All Sources"
                  ? papers.length
                  : papers.filter((p) => (paperFolderMap[p.paper_id] || "Custom Uploads") === f).length;
              const isActive = activeFolder === f;

              return (
                <div
                  key={f}
                  className={`px-2 py-0.5 text-[11px] rounded-full whitespace-nowrap transition-colors flex items-center gap-1 shrink-0 ${
                    isActive
                      ? "bg-indigo-600 text-white font-medium"
                      : isDark
                      ? "bg-slate-800/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                      : "bg-slate-200/80 hover:bg-slate-300 text-slate-700"
                  }`}
                >
                  <button type="button" onClick={() => setActiveFolder(f)} className="flex items-center gap-1 outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 rounded-full">
                    <span>{f}</span>
                  </button>
                  <span className={`text-[9px] px-1 rounded-full ${isActive ? "bg-indigo-700 text-white" : "text-slate-500"}`}>
                    {count}
                  </span>
                  {f !== "All Sources" && f !== "Custom Uploads" && (
                    <button type="button" onClick={() => handleDeleteFolder(f)} className={`ml-0.5 rounded-full p-1 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 ${isDark ? "text-rose-300 hover:bg-rose-500/20 hover:text-rose-200" : "text-rose-600 hover:bg-rose-100 hover:text-rose-700"}`} aria-label={`Delete ${f} folder`} title={`Delete ${f} folder`}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Paper List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredPapers.map((paper) => {
          const isSelected = selectedPaperIds.includes(paper.paper_id);
          const folder = paperFolderMap[paper.paper_id] || "Custom Uploads";

          return (
            <div
              key={paper.paper_id}
              className={`p-2.5 rounded-lg border transition-all cursor-pointer group ${
                isSelected
                  ? isDark
                    ? "bg-slate-900/90 border-indigo-500/60 shadow-xs"
                    : "bg-white border-indigo-500/60 shadow-xs"
                  : isDark
                  ? "bg-transparent border-transparent hover:bg-slate-900/50 hover:border-slate-800"
                  : "bg-transparent border-transparent hover:bg-white hover:border-slate-200"
              }`}
              onClick={() => onTogglePaper(paper.paper_id)}
            >
              <div className="flex items-start gap-2.5">
                {/* Checkbox */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onTogglePaper(paper.paper_id);
                  }}
                  className="mt-0.5 text-slate-400 hover:text-indigo-400 transition-colors shrink-0"
                >
                  {isSelected ? (
                    <CheckSquare className="w-4 h-4 text-indigo-500" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-500" />
                  )}
                </button>

                <div className="flex-1 min-w-0">
                  <h3
                    className={`text-xs font-medium leading-snug line-clamp-2 ${
                      isSelected
                        ? isDark
                          ? "text-white"
                          : "text-slate-950 font-semibold"
                        : isDark
                        ? "text-slate-300 group-hover:text-white"
                        : "text-slate-700 group-hover:text-slate-900"
                    }`}
                  >
                    {paper.title}
                  </h3>

                  {/* Clean metadata */}
                  <div className="mt-1 flex items-center gap-1.5 text-[11px] text-slate-500 flex-wrap">
                    {paper.source_url && <a href={paper.source_url} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()} className="inline-flex max-w-full items-center gap-1 truncate text-teal-500 hover:text-teal-400" title={paper.source_url}><Link2 className="h-3 w-3 shrink-0" /><span className="truncate">{new URL(paper.source_url).hostname}</span></a>}
                    {paper.source_url && <span aria-hidden="true">·</span>}
                    <span>{paper.num_entities || 16} entities</span>
                    <span aria-hidden="true">·</span>
                    <span>{paper.num_relations || 22} relations</span>
                    {activeFolder === "All Sources" && (
                      <>
                        <span aria-hidden="true">·</span>
                        <span className="text-[10px] text-slate-400 font-mono bg-slate-800/40 px-1 rounded">
                          {folder}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  {/* Summarize paper button */}
                  {onSummarizePaper && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSummarizePaper(paper);
                      }}
                      className={`opacity-0 group-hover:opacity-100 p-1 text-[10px] font-medium rounded transition-opacity ${
                        isDark
                          ? "bg-slate-800 hover:bg-amber-950/80 text-slate-400 hover:text-amber-300"
                          : "bg-slate-100 hover:bg-amber-50 text-slate-500 hover:text-amber-600"
                      }`}
                      title="Summarize Paper"
                    >
                      <Sparkles className="w-3 h-3 text-amber-400" />
                    </button>
                  )}

                  {/* "Focus Only" single selection trigger */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectOnlyPaper(paper.paper_id);
                    }}
                    className={`opacity-0 group-hover:opacity-100 px-1.5 py-0.5 text-[10px] font-medium rounded transition-opacity ${
                      isDark
                        ? "bg-slate-800 hover:bg-slate-700 text-slate-300"
                        : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                    }`}
                    title="Focus solely on this paper"
                  >
                    Only
                  </button>

                  {/* Delete source button */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeletePaper(paper.paper_id);
                    }}
                    className={`opacity-0 group-hover:opacity-100 p-1 text-[10px] font-medium rounded transition-opacity ${
                      isDark
                        ? "bg-slate-800/80 hover:bg-rose-950/80 text-slate-400 hover:text-rose-400 border border-transparent hover:border-rose-800/50"
                        : "bg-slate-100 hover:bg-rose-50 text-slate-500 hover:text-rose-600 border border-transparent hover:border-rose-200"
                    }`}
                    title="Remove paper from sources"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {filteredPapers.length === 0 && (
          <div className="p-6 text-center text-xs text-slate-500">
            No research papers in folder "{activeFolder}" matching "{searchQuery}"
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div
        className={`p-3 border-t text-[11px] text-slate-500 flex items-center justify-between ${
          isDark ? "border-slate-800/80 bg-slate-950" : "border-slate-200 bg-white"
        }`}
      >
        <span>Neo4j Synchronized</span>
        <span className="font-mono">{papers.length} Papers Total</span>
      </div>
    </aside>
  );
};
