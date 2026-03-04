import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Database, ArrowLeft, RefreshCw, Activity, Server } from "lucide-react";

interface RedisData {
  [key: string]: any;
}

const DataPage = () => {
  const [db1, setDb1] = useState<RedisData | null>(null);
  const [db2, setDb2] = useState<RedisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"db1" | "db2">("db1");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [res1, res2] = await Promise.all([
        fetch("http://localhost:8000/api/redis/db1"),
        fetch("http://localhost:8000/api/redis/db2"),
      ]);
      if (!res1.ok || !res2.ok) throw new Error("Failed to fetch Redis data");
      setDb1(await res1.json());
      setDb2(await res2.json());
    } catch (err: any) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const activeData = activeTab === "db1" ? db1 : db2;

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
          <button
            onClick={fetchData}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:brightness-110 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </header>

      <main className="container max-w-5xl mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {(["db1", "db2"] as const).map((db) => (
            <button
              key={db}
              onClick={() => setActiveTab(db)}
              className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition
                ${activeTab === db
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
            >
              <Server className="w-4 h-4" />
              Redis DB {db === "db1" ? "1 — Conversation Cache" : "2 — Health & Context"}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm mb-6">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Activity className="w-8 h-8 text-primary animate-spin" />
          </div>
        )}

        {/* Data display */}
        {!loading && activeData && (
          <motion.div
            key={activeTab}
            className="clinical-card-elevated overflow-hidden"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {Object.keys(activeData).length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <Database className="w-10 h-10 mx-auto mb-3 opacity-40" />
                <p>No data in this database.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/50">
                      <th className="text-left px-4 py-3 font-semibold text-foreground">Key</th>
                      <th className="text-left px-4 py-3 font-semibold text-foreground">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(activeData).map(([key, val], i) => (
                      <tr key={key} className={`border-b border-border ${i % 2 === 0 ? "" : "bg-muted/20"}`}>
                        <td className="px-4 py-3 font-mono text-xs text-primary font-medium whitespace-nowrap">
                          {key}
                        </td>
                        <td className="px-4 py-3 text-foreground">
                          <pre className="text-xs font-mono whitespace-pre-wrap break-all max-w-xl">
                            {typeof val === "object" ? JSON.stringify(val, null, 2) : String(val)}
                          </pre>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </motion.div>
        )}

        {/* No data fetched yet */}
        {!loading && !activeData && !error && (
          <div className="text-center py-20 text-muted-foreground">
            <Database className="w-10 h-10 mx-auto mb-3 opacity-40" />
            <p>Click Refresh to load data from Redis.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default DataPage;
