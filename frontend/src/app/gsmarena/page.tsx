"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type SearchResult = { name: string; url: string; img_src?: string };

const SEARCH_COOLDOWN_SEC = 20;
const COOLDOWN_AFTER_429_SEC = 180;

export default function GsmArenaPage() {
  const [keyword, setKeyword] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [importing, setImporting] = useState<string | null>(null);
  const [duplicateAction, setDuplicateAction] = useState<"overwrite" | "new_version" | "cancel">("overwrite");
  const [cooldownRemain, setCooldownRemain] = useState(0);

  useEffect(() => {
    if (cooldownRemain <= 0) return;
    const t = setInterval(() => setCooldownRemain((c) => (c <= 1 ? 0 : c - 1)), 1000);
    return () => clearInterval(t);
  }, [cooldownRemain]);

  const handleSearch = async () => {
    if (!keyword.trim()) {
      setMessage({ type: "err", text: "请输入机型关键词" });
      return;
    }
    if (cooldownRemain > 0) return;
    setLoading(true);
    setMessage(null);
    setResults([]);
    try {
      const res = await api<{ results: SearchResult[]; message?: string }>(
        `/api/gsmarena/search?q=${encodeURIComponent(keyword.trim())}`
      );
      const resultsList = (res as { results?: SearchResult[] }).results ?? [];
      const errMsg = (res as { message?: string }).message ?? "";
      if (res.success && resultsList.length) {
        setResults(resultsList);
        setMessage({ type: "ok", text: `找到 ${resultsList.length} 个候选，请选择一条导入` });
        setCooldownRemain(SEARCH_COOLDOWN_SEC);
      } else {
        setMessage({ type: "err", text: errMsg || "未找到结果" });
        if (errMsg.includes("429") || errMsg.includes("过于频繁")) {
          setCooldownRemain(COOLDOWN_AFTER_429_SEC);
        } else {
          setCooldownRemain(SEARCH_COOLDOWN_SEC);
        }
      }
    } catch (e) {
      const text = e instanceof Error ? e.message : "搜索失败";
      setMessage({ type: "err", text });
      if (text.includes("429") || text.includes("过于频繁")) {
        setCooldownRemain(COOLDOWN_AFTER_429_SEC);
      } else {
        setCooldownRemain(SEARCH_COOLDOWN_SEC);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (url: string) => {
    setImporting(url);
    setMessage(null);
    const base = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    try {
      const res = await fetch(
        `${base}/api/gsmarena/import?duplicate_action=${duplicateAction}`,
        { method: "POST", body: JSON.stringify({ url }), headers: { "Content-Type": "application/json" } }
      ).then((r) => r.json()) as { success: boolean; message?: string };
      if (res.success) {
        setMessage({ type: "ok", text: res.message || "导入成功" });
      } else {
        setMessage({ type: "err", text: res.message || "导入失败" });
      }
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : "导入失败" });
    } finally {
      setImporting(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">GSMArena 查询导入</h1>
        <p className="mt-1 text-gray-600">输入机型关键词（如 Xiaomi 14、vivo X100），选择候选后导入数据库。</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>搜索机型</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-2">
          <Input
            placeholder="输入型号关键词"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !loading && cooldownRemain <= 0 && handleSearch()}
          />
          <Button
            onClick={handleSearch}
            disabled={loading || cooldownRemain > 0}
          >
            {loading ? "搜索中…" : cooldownRemain > 0 ? `请 ${cooldownRemain} 秒后再试` : "搜索"}
          </Button>
        </CardContent>
      </Card>

      {message && (
        <div className={`rounded-md p-3 ${message.type === "ok" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}>
          {message.text}
        </div>
      )}

      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>候选列表（点击「导入」写入数据库）</CardTitle>
            <div className="flex items-center gap-2 text-sm">
              <span>若已存在同型号：</span>
              <select
                className="rounded border px-2 py-1"
                value={duplicateAction}
                onChange={(e) => setDuplicateAction(e.target.value as "overwrite" | "new_version" | "cancel")}
              >
                <option value="overwrite">覆盖更新</option>
                <option value="new_version">另存为新版本</option>
                <option value="cancel">取消</option>
              </select>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {results.map((r) => (
                <li key={r.url} className="flex items-center justify-between rounded border p-2">
                  <span>{r.name}</span>
                  <Button
                    size="sm"
                    disabled={importing !== null}
                    onClick={() => handleImport(r.url)}
                  >
                    {importing === r.url ? "导入中…" : "导入"}
                  </Button>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
