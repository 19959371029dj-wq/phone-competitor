"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ProductDetail = {
  id: number;
  brand?: string;
  model?: string;
  full_name?: string;
  slug?: string;
  source_type?: string;
  source_url?: string;
  launch_date?: string;
  status?: string;
  os?: string;
  chipset?: string;
  cpu?: string;
  gpu?: string;
  display_type?: string;
  display_size?: string;
  resolution?: string;
  refresh_rate?: string;
  battery?: string;
  charging?: string;
  main_camera?: string;
  selfie_camera?: string;
  memory_summary?: string;
  price?: number;
  currency?: string;
  market_region?: string;
  sales_channel?: string;
  raw_specs_json?: string;
  raw_html?: string;
  updated_at?: string;
  spec_items?: { spec_group?: string; spec_key?: string; spec_value?: string }[];
};

const FIELDS: { key: keyof ProductDetail; label: string; group: string }[] = [
  { key: "brand", label: "品牌", group: "基本信息" },
  { key: "model", label: "型号", group: "基本信息" },
  { key: "full_name", label: "完整名称", group: "基本信息" },
  { key: "launch_date", label: "发布时间", group: "基本信息" },
  { key: "status", label: "状态", group: "基本信息" },
  { key: "display_type", label: "屏幕类型", group: "屏幕" },
  { key: "display_size", label: "屏幕尺寸", group: "屏幕" },
  { key: "resolution", label: "分辨率", group: "屏幕" },
  { key: "refresh_rate", label: "刷新率", group: "屏幕" },
  { key: "os", label: "系统", group: "性能" },
  { key: "chipset", label: "芯片", group: "性能" },
  { key: "cpu", label: "CPU", group: "性能" },
  { key: "gpu", label: "GPU", group: "性能" },
  { key: "memory_summary", label: "内存/存储", group: "性能" },
  { key: "main_camera", label: "主摄", group: "影像" },
  { key: "selfie_camera", label: "前摄", group: "影像" },
  { key: "battery", label: "电池", group: "电池" },
  { key: "charging", label: "充电", group: "电池" },
  { key: "price", label: "价格", group: "价格" },
  { key: "currency", label: "币种", group: "价格" },
  { key: "market_region", label: "市场区域", group: "价格" },
  { key: "sales_channel", label: "渠道", group: "价格" },
];

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [data, setData] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    if (!id) return;
    api<{ data: ProductDetail }>(`/api/products/${id}`)
      .then((res) => setData((res as { data?: ProductDetail }).data ?? null))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [id]);

  const update = (key: keyof ProductDetail, value: string | number | undefined) => {
    if (!data) return;
    setData({ ...data, [key]: value });
  };

  const handleSave = async () => {
    if (!data) return;
    setSaving(true);
    setMessage(null);
    try {
      const body: Record<string, unknown> = {};
      FIELDS.forEach((f) => {
        const v = data[f.key];
        if (v !== undefined) body[f.key] = v;
      });
      await api(`/api/products/${id}`, { method: "PUT", body: JSON.stringify(body) });
      setMessage({ type: "ok", text: "已保存" });
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : "保存失败" });
    } finally {
      setSaving(false);
    }
  };

  const handleDuplicate = async () => {
    try {
      const res = await api<{ id: number }>(`/api/products/${id}/duplicate`, { method: "POST", body: JSON.stringify({}) });
      if (res.id) router.push(`/products/${res.id}`);
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : "复制失败" });
    }
  };

  const handleDelete = async () => {
    if (!confirm("确定删除该机型？")) return;
    try {
      await api(`/api/products/${id}`, { method: "DELETE" });
      router.push("/products");
    } catch (e) {
      setMessage({ type: "err", text: e instanceof Error ? e.message : "删除失败" });
    }
  };

  if (loading || !data) {
    return <div className="py-8">{loading ? "加载中…" : "未找到该机型"}</div>;
  }

  const groups = Array.from(new Set(FIELDS.map((f) => f.group)));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">机型详情 — {data.full_name || data.model || data.id}</h1>
          <p className="mt-1 text-gray-600">编辑后点击保存；可复制为新品或删除。</p>
        </div>
        <div className="flex gap-2">
          <Link href="/products"><Button variant="outline">返回列表</Button></Link>
          <Button variant="secondary" onClick={handleDuplicate}>复制为新记录</Button>
          <Button variant="destructive" onClick={handleDelete}>删除</Button>
          <Button onClick={handleSave} disabled={saving}>{saving ? "保存中…" : "保存"}</Button>
        </div>
      </div>

      {message && (
        <div className={`rounded-md p-3 ${message.type === "ok" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}>
          {message.text}
        </div>
      )}

      {groups.map((group) => (
        <Card key={group}>
          <CardHeader>
            <CardTitle>{group}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-2">
            {FIELDS.filter((f) => f.group === group).map((f) => (
              <div key={f.key}>
                <label className="text-sm text-gray-600">{f.label}</label>
                <Input
                  className="mt-0.5"
                  value={String(data[f.key] ?? "")}
                  onChange={(e) => update(f.key, e.target.value)}
                />
              </div>
            ))}
          </CardContent>
        </Card>
      ))}

      {data.source_url && (
        <Card>
          <CardHeader>
            <CardTitle>来源</CardTitle>
          </CardHeader>
          <CardContent>
            <a href={data.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">{data.source_url}</a>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
