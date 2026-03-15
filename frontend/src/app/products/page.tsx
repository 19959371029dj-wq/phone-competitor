"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, apiUpload } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Product = { id: number; brand?: string; model?: string; full_name?: string; source_type?: string; price?: number; currency?: string; launch_date?: string; updated_at: string };

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function ProductsPage() {
  const [list, setList] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [brand, setBrand] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const handleDownloadProductTemplate = () => {
    window.open(`${API_BASE}/api/import/product-template`, "_blank");
  };

  const handleUploadProducts = async () => {
    if (!uploadFile) {
      setUploadMsg({ type: "err", text: "请选择 Excel/CSV 模板文件" });
      return;
    }
    setUploading(true);
    setUploadMsg(null);
    try {
      const res = await apiUpload<{ created?: number; message?: string }>(
        "/api/import/products-upload",
        uploadFile
      );
      if (res.success) {
        setUploadMsg({ type: "ok", text: res.message || `已导入 ${res.created ?? 0} 条机型` });
        setUploadFile(null);
        load(0);
      } else {
        setUploadMsg({ type: "err", text: res.message || "导入失败" });
      }
    } catch (e) {
      setUploadMsg({ type: "err", text: e instanceof Error ? e.message : "导入失败" });
    } finally {
      setUploading(false);
    }
  };

  const load = (skip = 0) => {
    setLoading(true);
    const params = new URLSearchParams({ limit: "50", skip: String(skip) });
    if (search) params.set("search", search);
    if (brand) params.set("brand", brand);
    api<{ data: Product[]; total: number }>(`/api/products?${params}`)
      .then((res) => {
        const r = res as { data?: Product[]; total?: number };
        setList(r.data ?? []);
        setTotal(r.total ?? 0);
      })
      .catch(() => setList([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load(0);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">产品数据库</h1>
        <p className="mt-1 text-gray-600">查看、搜索、编辑已入库机型；支持下载模板批量导入（与 GSMArena 字段一致）。</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>使用模板批量导入</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-gray-600">下载 Excel 模板，按列填写机型信息后上传，将批量写入产品库（与 GSMArena 导入字段一致）。</p>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" onClick={handleDownloadProductTemplate}>
              下载产品模板
            </Button>
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              className="text-sm"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              disabled={uploading}
            />
            <Button onClick={handleUploadProducts} disabled={uploading}>
              {uploading ? "导入中…" : "上传并导入"}
            </Button>
          </div>
          {uploadMsg && (
            <div className={`rounded-md p-2 text-sm ${uploadMsg.type === "ok" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}>
              {uploadMsg.text}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>搜索与筛选</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Input
            placeholder="关键词"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-40"
          />
          <Input
            placeholder="品牌"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            className="w-32"
          />
          <Button onClick={() => load()}>查询</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>机型列表（共 {total} 条）</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-gray-500">加载中…</p>
          ) : list.length === 0 ? (
            <p className="text-gray-500">暂无数据</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="p-2 text-left">ID</th>
                    <th className="p-2 text-left">品牌</th>
                    <th className="p-2 text-left">型号</th>
                    <th className="p-2 text-left">名称</th>
                    <th className="p-2 text-left">价格</th>
                    <th className="p-2 text-left">更新时间</th>
                    <th className="p-2 text-left">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((p) => (
                    <tr key={p.id} className="border-b">
                      <td className="p-2">{p.id}</td>
                      <td className="p-2">{p.brand ?? "-"}</td>
                      <td className="p-2">{p.model ?? "-"}</td>
                      <td className="p-2">{p.full_name ?? "-"}</td>
                      <td className="p-2">{p.price != null ? `${p.price} ${p.currency || ""}` : "-"}</td>
                      <td className="p-2">{p.updated_at ? new Date(p.updated_at).toLocaleString() : "-"}</td>
                      <td className="p-2">
                        <Link href={`/products/${p.id}`}><Button size="sm" variant="outline">详情/编辑</Button></Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
