import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { Database, ArrowLeft, RefreshCw, Activity, Server, ChevronDown, ChevronUp } from "lucide-react";

const DataPage = () => {
  const [db0, setDb0] = useState<any>(null);
  const [db1, setDb1] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"db0" | "db1">("db0");
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRow = (key: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedRows(newExpanded);
  };

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Add timeout to prevent infinite loading
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const [res0, res1] = await Promise.all([
        fetch("http://localhost:8000/api/redis/db0", { signal: controller.signal }),
        fetch("http://localhost:8000/api/redis/db1", { signal: controller.signal }),
      ]);

      clearTimeout(timeoutId);

      if (!res0.ok || !res1.ok) {
        const errorText = !res0.ok ? await res0.text() : await res1.text();
        throw new Error(`API Error: ${errorText}`);
      }

      const data0 = await res0.json();
      const data1 = await res1.json();

      setDb0(data0);
      setDb1(data1);
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setError("Request timed out. Make sure the backend is running.");
      } else {
        setError(err.message || "Failed to load data");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const activeData = activeTab === "db0" ? db0 : db1;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="container max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-base font-bold text-foreground flex items-center gap-2">
              <Database className="w-4 h-4 text-primary" />
              Redis Data Explorer
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchData()}
              disabled={loading}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:brightness-110 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="container max-w-5xl mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab("db0")}
            className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition ${activeTab === "db0"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
          >
            <Server className="w-4 h-4" />
            Redis DB 0 — Conversation Cache
          </button>
          <button
            onClick={() => setActiveTab("db1")}
            className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition ${activeTab === "db1"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
          >
            <Server className="w-4 h-4" />
            Redis DB 1 — Tool Retrieval Cache
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Activity className="w-8 h-8 text-primary animate-spin mb-4" />
            <p className="text-sm text-muted-foreground">Loading Redis data...</p>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="p-6 rounded-xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-900 dark:text-red-100 mb-6">
            <p className="font-semibold mb-2">Error loading Redis data</p>
            <p className="text-sm mb-3">{error}</p>
            <p className="text-xs">Make sure Redis and the backend are running.</p>
          </div>
        )}

        {/* Summary Stats */}
        {!loading && !error && activeData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 rounded-lg border border-border bg-card">
              <div className="text-sm text-muted-foreground mb-1">Total Keys</div>
              <div className="text-2xl font-bold text-foreground">{activeData.total_keys || 0}</div>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <div className="text-sm text-muted-foreground mb-1">Memory Usage</div>
              <div className="text-2xl font-bold text-foreground">{activeData.memory_usage || "N/A"}</div>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <div className="text-sm text-muted-foreground mb-1">TTL</div>
              <div className="text-2xl font-bold text-foreground">{activeTab === "db0" ? "30h" : "36h"}</div>
            </div>
          </div>
        )}

        {/* Data Table */}
        {!loading && !error && activeData && (
          <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
            {activeData.entries && activeData.entries.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <Database className="w-10 h-10 mx-auto mb-3 opacity-40" />
                <p>No data in {activeData.db_name || "this database"}.</p>
                <p className="text-xs mt-2">
                  {activeTab === "db0"
                    ? "Start a conversation to see data here."
                    : "Make queries to populate the cache."}
                </p>
              </div>
            ) : activeData.entries ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/50">
                      <th className="text-left px-4 py-3 font-semibold text-foreground">Key</th>
                      <th className="text-left px-4 py-3 font-semibold text-foreground">Type</th>
                      <th className="text-left px-4 py-3 font-semibold text-foreground">Info</th>
                      <th className="text-left px-4 py-3 font-semibold text-foreground">Last Active</th>
                      <th className="text-left px-4 py-3 font-semibold text-foreground">Expires In</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeData.entries.map((entry: any, i: number) => {
                      const isExpanded = expandedRows.has(entry.key);
                      return (
                        <React.Fragment key={entry.key || i}>
                          <tr className={`border-b border-border ${i % 2 === 0 ? "" : "bg-muted/20"} cursor-pointer hover:bg-muted/30`} onClick={() => toggleRow(entry.key)}>
                            <td className="px-4 py-3 font-mono text-xs text-primary font-medium">
                              <div className="flex items-center gap-2">
                                {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                {entry.key}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-foreground">
                              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-primary/10 text-primary">
                                {entry.type || entry.tool_name}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-foreground text-xs">
                              {activeTab === "db0" ? (
                                <span>{entry.message_count || 0} messages</span>
                              ) : (
                                <span>{entry.query_info || "N/A"}</span>
                              )}
                            </td>
                            {/* Last Active */}
                            <td className="px-4 py-3 text-xs">
                              <span className="text-foreground font-medium">
                                {entry.last_active_str || "—"}
                              </span>
                            </td>
                            {/* Expires In */}
                            <td className="px-4 py-3 text-xs">
                              {entry.ttl_seconds === -1 ? (
                                <span className="text-muted-foreground">No expiry</span>
                              ) : (
                                <span className={`font-mono ${entry.ttl_seconds < 3600
                                  ? "text-red-500"
                                  : entry.ttl_seconds < 21600
                                    ? "text-yellow-500"
                                    : "text-green-500"
                                  }`}>
                                  {Math.floor(entry.ttl_seconds / 3600)}h{" "}
                                  {Math.floor((entry.ttl_seconds % 3600) / 60)}m
                                </span>
                              )}
                            </td>
                          </tr>
                          <AnimatePresence>
                            {isExpanded && (
                              <motion.tr
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                className="border-b border-border bg-muted/10"
                              >
                                <td colSpan={4} className="px-4 py-4">
                                  <div className="space-y-2">
                                    <p className="text-xs font-semibold text-muted-foreground mb-2">
                                      {activeTab === "db0" ? "Conversation History:" : "Cached Data:"}
                                    </p>
                                    {activeTab === "db0" && entry.preview && entry.preview.length > 0 ? (() => {
                                      const total = entry.preview.length;
                                      // max(6, 60%) rounded up to the nearest even number to keep pairs unbroken
                                      const displayCount = Math.max(6, Math.ceil((total * 0.6) / 2) * 2);
                                      const messagesToShow = total > displayCount ? entry.preview.slice(-displayCount) : entry.preview;
                                      const hiddenCount = total - messagesToShow.length;

                                      return (
                                        <div className="space-y-2">
                                          {hiddenCount > 0 && (
                                            <div className="p-2 text-center text-xs text-muted-foreground bg-muted/20 border border-dashed border-border rounded-lg">
                                              🔼 {hiddenCount} older messages hidden
                                            </div>
                                          )}
                                          {messagesToShow.map((msg: any, idx: number) => (
                                            <div key={idx} className="p-3 rounded-lg bg-background border border-border">
                                              <div className="flex items-start gap-2">
                                                <span className={`text-xs font-semibold px-2 py-1 rounded ${msg.role === "user"
                                                  ? "bg-blue-500/10 text-blue-500"
                                                  : "bg-green-500/10 text-green-500"
                                                  }`}>
                                                  {msg.role || "system"}
                                                </span>
                                                <p className="text-xs text-foreground flex-1">{msg.content || msg.data}</p>
                                              </div>
                                            </div>
                                          ))}
                                        </div>
                                      );
                                    })() : activeTab === "db1" && entry.data_preview ? (
                                      <div className="p-3 rounded-lg bg-background border border-border">
                                        <pre className="text-xs text-foreground whitespace-pre-wrap">
                                          {JSON.stringify(entry.data_preview, null, 2)}
                                        </pre>
                                      </div>
                                    ) : (
                                      <p className="text-xs text-muted-foreground italic">No preview available</p>
                                    )}
                                  </div>
                                </td>
                              </motion.tr>
                            )}
                          </AnimatePresence>
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        )}
      </main>
    </div>
  );
};

export default DataPage;
