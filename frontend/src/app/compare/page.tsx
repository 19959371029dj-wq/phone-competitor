"use client";

import { useState, useEffect, useMemo } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const MAX_SELECT = 10;
type Product = { id: number; full_name?: string; brand?: string; model?: string };

export default function ComparePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [brands, setBrands] = useState<string[]>([]);
  const [brandFilter, setBrandFilter] = useState<string>("");
  const [modelKeyword, setModelKeyword] = useState<string>("");
  const [selected, setSelected] = useState<number[]>([]);
  const [table, setTable] = useState<{ product_headers: { id: number; full_name?: string }[]; rows: { spec_key: string; spec_group: string; values: string[] }[] } | null>(null);
  const [report, setReport] = useState<string | null>(null);
  const [loadingTable, setLoadingTable] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    api<{ data: Product[] }>("/api/products?limit=500")
      .then((res) => setProducts((res as { data?: Product[] }).data ?? []))
      .catch(() => setProducts([]));
    api<{ data: string[] }>("/api/products/brands")
      .then((res) => setBrands((res as { data?: string[] }).data ?? []))
      .catch(() => setBrands([]));
  }, []);

  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      if (brandFilter && (p.brand || "") !== brandFilter) return false;
      if (modelKeyword) {
        const kw = modelKeyword.trim().toLowerCase();
        const name = (p.full_name || p.model || p.brand || "").toLowerCase();
        if (!name.includes(kw)) return false;
      }
      return true;
    });
  }, [products, brandFilter, modelKeyword]);

  const toggle = (id: number) => {
    if (selected.includes(id)) {
      setSelected(selected.filter((x) => x !== id));
    } else if (selected.length < MAX_SELECT) {
      setSelected([...selected, id]);
    }
  };

  const loadTable = async () => {
    if (selected.length < 2) {
      setMessage({ type: "err", text: "请至少选择 2 个机型" });
      return;
    }
    setLoadingTable(true);
    setMessage(null);
    setTable(null);
    try {
      const res = await api<{ product_headers: unknown[]; rows: unknown[] }>("/api/compare/table", {
        method: "POST",
        body: JSON.stringify({ product_ids: selected }),
      });
      if (res.success && res.product_headers && res.rows) {
        setTable({
          product_headers: res.product_headers as { id: number; full_name?: string }[],
          rows: res.rows as { spec_key: string; spec_group: string; values: string[] }[],
        });
      }
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : "加载对比表失败" });
    } finally {
      setLoadingTable(false);
    }
  };

  const generateReport = async () => {
    if (selected.length < 2) {
      setMessage({ type: "err", text: "请至少选择 2 个机型" });
      return;
    }
    setLoadingReport(true);
    setMessage(null);
    setReport(null);
    try {
      const res = await api<{ report_markdown?: string; message?: string }>("/api/compare/report", {
        method: "POST",
        body: JSON.stringify({ product_ids: selected }),
      });
      const md = (res as { report_markdown?: string }).report_markdown;
      if (res.success && md) {
        setReport(md);
        setMessage({ type: "ok", text: "报告已生成（需配置 DeepSeek API Key）" });
      } else {
        setMessage({ type: "err", text: res.message || "生成失败" });
      }
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : "生成失败" });
    } finally {
      setLoadingReport(false);
    }
  };

  const copyReport = () => {
    if (report) {
      navigator.clipboard.writeText(report);
      setMessage({ type: "ok", text: "已复制到剪贴板" });
    }
  };

  const downloadCompareTable = () => {
    if (selected.length < 2) {
      setMessage({ type: "err", text: "请至少选择 2 个机型" });
      return;
    }
    const base = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const url = `${base}/api/compare/export?product_ids=${selected.join(",")}`;
    window.open(url, "_blank");
    setMessage({ type: "ok", text: "正在下载对比表 Excel" });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">竞品分析</h1>
        <p className="mt-1 text-gray-600">选择 2～10 个机型，生成参数对比表与 AI 竞品分析报告。先按品牌筛选，再按型号关键词缩小范围。</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>选择机型</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2">
              <span className="text-sm text-gray-600">品牌：</span>
              <select
                className="rounded border border-gray-300 px-2 py-1.5 text-sm"
                value={brandFilter}
                onChange={(e) => setBrandFilter(e.target.value)}
              >
                <option value="">全部品牌</option>
                {brands.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2">
              <span className="text-sm text-gray-600">型号关键词：</span>
              <Input
                placeholder="输入型号或名称筛选"
                value={modelKeyword}
                onChange={(e) => setModelKeyword(e.target.value)}
                className="w-48"
              />
            </label>
          </div>
          <p className="text-sm text-gray-600">已选 {selected.length} / {MAX_SELECT}，当前显示 {filteredProducts.length} 款机型</p>
          <div className="max-h-64 overflow-y-auto rounded border border-gray-200 p-2">
            <div className="flex flex-wrap gap-x-4 gap-y-1">
              {filteredProducts.length === 0 ? (
                <p className="text-sm text-gray-500">暂无符合条件的机型，请调整品牌或关键词。</p>
              ) : (
                filteredProducts.map((p) => (
                  <label key={p.id} className="flex items-center gap-1.5 cursor-pointer hover:bg-gray-50 rounded px-1 py-0.5">
                    <input
                      type="checkbox"
                      checked={selected.includes(p.id)}
                      onChange={() => toggle(p.id)}
                    />
                    <span className="text-sm">{p.full_name || p.model || p.id}</span>
                  </label>
                ))
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={loadTable} disabled={loadingTable || selected.length < 2}>
              {loadingTable ? "加载中…" : "生成对比表"}
            </Button>
            <Button variant="outline" onClick={downloadCompareTable} disabled={selected.length < 2}>
              下载对比表
            </Button>
            <Button onClick={generateReport} disabled={loadingReport || selected.length < 2}>
              {loadingReport ? "生成中…" : "生成 AI 竞品分析"}
            </Button>
          </div>
          <p className="text-sm text-gray-500">选择 2～10 个机型后，可生成页面对比表或直接下载 Excel 对比表。</p>
        </CardContent>
      </Card>

      {message && (
        <div className={`rounded-md p-3 ${message.type === "ok" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}>
          {message.text}
        </div>
      )}

      {table && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>参数对比表</CardTitle>
            <Button size="sm" variant="outline" onClick={downloadCompareTable}>下载对比表</Button>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">参数</th>
                  {table.product_headers.map((h) => (
                    <th key={h.id} className="p-2 text-left max-w-[200px]">{h.full_name || h.id}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((r, i) => (
                  <tr key={i} className="border-b">
                    <td className="p-2 font-medium">{r.spec_group} / {r.spec_key}</td>
                    {r.values.map((v, j) => (
                      <td key={j} className="p-2 max-w-[200px] break-words">{v || "-"}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {report && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>AI 竞品分析报告</CardTitle>
            <Button size="sm" variant="outline" onClick={copyReport}>复制报告</Button>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap rounded border bg-gray-50 p-4 text-sm max-h-[60vh] overflow-auto">{report}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
