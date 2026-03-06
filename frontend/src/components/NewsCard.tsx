import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Newspaper, ExternalLink, ChevronDown, ChevronUp, Calendar, Radio } from "lucide-react";
import type { NewsData } from "@/types/clinical";

interface NewsCardProps {
    data: NewsData;
    textResponse: string;
}

const formatDate = (dateStr: string) => {
    try {
        return new Date(dateStr).toLocaleDateString("en-US", {
            month: "short", day: "numeric", year: "numeric"
        });
    } catch {
        return dateStr;
    }
};

const NewsCard = ({ data, textResponse }: NewsCardProps) => {
    const [expandedIdx, setExpandedIdx] = useState<number | null>(0);

    const articles = data.articles.filter((a) => a.valid);

    return (
        <div className="space-y-4">
            {/* AI spoken summary */}
            <p className="text-foreground leading-relaxed text-sm">{textResponse}</p>

            {/* Header bar */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-blue-500/15 flex items-center justify-center">
                        <Radio className="w-3.5 h-3.5 text-blue-400" />
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-foreground capitalize">
                            {data.topic}
                        </p>
                        <p className="text-xs text-muted-foreground">
                            {articles.length} article{articles.length !== 1 ? "s" : ""} · {data.source ?? "NewsAPI"}
                        </p>
                    </div>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-blue-500/10 text-blue-400 font-medium border border-blue-500/20">
                    Live News
                </span>
            </div>

            {/* Article cards */}
            {articles.length === 0 ? (
                <div className="p-4 rounded-xl bg-muted/40 border border-border text-sm text-muted-foreground text-center">
                    {data.message ?? "No articles found for this topic."}
                </div>
            ) : (
                <div className="space-y-2">
                    {articles.map((article, i) => {
                        const isExpanded = expandedIdx === i;
                        return (
                            <motion.div
                                key={i}
                                className="rounded-xl border border-border bg-muted/30 hover:bg-muted/50 transition-colors overflow-hidden"
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.08 }}
                            >
                                {/* Article header — always visible */}
                                <button
                                    className="w-full flex items-start gap-3 p-3.5 text-left"
                                    onClick={() => setExpandedIdx(isExpanded ? null : i)}
                                >
                                    {/* Index badge */}
                                    <span className="shrink-0 mt-0.5 w-6 h-6 rounded-md bg-blue-500/15 text-blue-400 text-xs font-bold flex items-center justify-center">
                                        {i + 1}
                                    </span>

                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-semibold text-foreground line-clamp-2 leading-snug">
                                            {article.title}
                                        </p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                <Newspaper className="w-3 h-3" />
                                                {article.source}
                                            </span>
                                            <span className="text-muted-foreground/50">·</span>
                                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                <Calendar className="w-3 h-3" />
                                                {formatDate(article.date)}
                                            </span>
                                        </div>
                                    </div>

                                    <span className="shrink-0 text-muted-foreground mt-1">
                                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                    </span>
                                </button>

                                {/* Expanded summary */}
                                <AnimatePresence>
                                    {isExpanded && (
                                        <motion.div
                                            key="body"
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.25 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="px-4 pb-4 space-y-3 border-t border-border/50 pt-3">
                                                <p className="text-sm text-foreground leading-relaxed whitespace-pre-line">
                                                    {article.summary}
                                                </p>
                                                {article.url && (
                                                    <a
                                                        href={article.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                                                    >
                                                        <ExternalLink className="w-3 h-3" />
                                                        Read full article
                                                    </a>
                                                )}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default NewsCard;
