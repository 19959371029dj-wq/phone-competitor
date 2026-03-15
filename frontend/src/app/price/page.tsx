"use client";

import { useState, useEffect } from "react";
import { api, apiUpload } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type PreviewRow = {
  row_index: number;
  brand?: string;
  model?: string;
  full_name?: string;
  price: number;
  currency?: string;
  match_status: string;
  matched_product_id?: number;
  matched_full_name?: string;
};

type Batch = { id: number; import_type: string; file_name?: string; status?: string; summary?: string; created_at?: string };

export default function PricePage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<{ rows: PreviewRow[]; matched_count: number; no_match_count: number; duplicate_count: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [rollbackId, setRollbackId] = useState<number | null>(null);

  const loadBatches = () => {
    api<{ data: Batch[] }>("/api/import/batches")
      .then((res) => setBatches((res as { data?: Batch[] }).data ?? []))
      .catch(() => setBatches([]));
  };

  useEffect(() => {
    loadBatches();
  }, []);

  const handleDownloadTemplate = () => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/api/import/price-template`, "_blank");
  };

  const handlePreview = async () => {
    if (!file) {
      setMessage({ type: "err", text: "请选择 Excel/CSV 文件" });
      return;
    }
    setLoading(true);
    setMessage(null);
    setPreview(null);
    try {
      const res = await apiUpload<{ rows: PreviewRow[]; matched_count: number; no_match_count: number; duplicate_count: number }>(
        "/api/import/price-preview",
        file
      );
      const r = res as { rows?: PreviewRow[]; matched_count?: number; no_match_count?: number; duplicate_count?: number; message?: string };
      if (res.success && r.rows?.length) {
        setPreview({
          rows: r.rows,
          matched_count: r.matched_count ?? 0,
          no_match_count: r.no_match_count ?? 0,
          duplicate_count: r.duplicate_count ?? 0,
        });
        setMessage({ type: "ok", text: `匹配 ${r.matched_count} 条，未匹配 ${r.no_match_count} 条，重复 ${r.duplicate_count} 条` });
      } else {
        setMessage({ type: "err", text: r.message || "解析失败" });
      }
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : "上传失败" });
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!preview?.rows?.length) return;
    setConfirming(true);
    setMessage(null);
    try {
      const res = await api<{ batch_id?: number; updated_count?: number; message?: string }>("/api/import/price-confirm", {
        method: "POST",
        body: JSON.stringify({ rows: preview.rows }),
      });
      if (res.success) {
        setMessage({ type: "ok", text: res.message || "价格已更新" });
        setPreview(null);
        setFile(null);
        loadBatches();
      } else {
        setMessage({ type: "err", text: res.message || "更新失败" });
      }
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : "更新失败" });
    } finally {
      setConfirming(false);
    }
  };

  const handleRollback = async (batchId: number) => {
    if (!confirm("确定回滚该批次？")) return;
    setRollbackId(batchId);
    setMessage(null);
    try {
      await api(`/api/import/price-rollback/${batchId}`, { method: "POST" });
      setMessage({ type: "ok", text: "回滚成功" });
      loadBatches();
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : "回滚失败" });
    } finally {
      setRollbackId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">价格批量更新</h1>
        <p className="mt-1 text-gray-600">下载模板、上传 Excel/CSV，预览匹配结果后确认更新；支持回滚最近导入。</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>模板与上传</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={handleDownloadTemplate}>下载模板</Button>
          <input
            type="file"
            accept=".xlsx,.xls,.csv"
            className="text-sm"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <Button onClick={handlePreview} disabled={loading}>{loading ? "解析中…" : "预览匹配"}</Button>
        </CardContent>
      </Card>

      {message && (
        <div className={`rounded-md p-3 ${message.type === "ok" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}>
          {message.text}
        </div>
      )}

      {preview && (
        <Card>
          <CardHeader>
            <CardTitle>匹配结果预览</CardTitle>
            <p className="text-sm text-gray-600">匹配 {preview.matched_count} / 未匹配 {preview.no_match_count} / 重复 {preview.duplicate_count}</p>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="max-h-64 overflow-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="p-1 text-left">行</th>
                    <th className="p-1 text-left">品牌/型号/名称</th>
                    <th className="p-1 text-left">价格</th>
                    <th className="p-1 text-left">状态</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.slice(0, 20).map((r) => (
                    <tr key={r.row_index} className="border-b">
                      <td className="p-1">{r.row_index}</td>
                      <td className="p-1">{r.full_name || `${r.brand} ${r.model}`}</td>
                      <td className="p-1">{r.price} {r.currency}</td>
                      <td className="p-1">{r.match_status === "matched" ? "✓" : r.match_status === "no_match" ? "未匹配" : "重复"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {preview.rows.length > 20 && <p className="text-sm text-gray-500">仅显示前 20 条…</p>}
            </div>
            <Button onClick={handleConfirm} disabled={confirming}>{confirming ? "更新中…" : "确认更新"}</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>最近导入批次</CardTitle>
        </CardHeader>
        <CardContent>
          {batches.length === 0 ? (
            <p className="text-gray-500">暂无批次</p>
          ) : (
            <ul className="space-y-2">
              {batches.map((b) => (
                <li key={b.id} className="flex items-center justify-between rounded border p-2">
                  <span>#{b.id} {b.file_name || b.import_type} — {b.status} {b.summary}</span>
                  {b.status === "success" && (
                    <Button size="sm" variant="outline" disabled={rollbackId !== null} onClick={() => handleRollback(b.id)}>
                      {rollbackId === b.id ? "回滚中…" : "回滚"}
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
