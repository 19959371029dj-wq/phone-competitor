"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  const [stats, setStats] = useState<{ total: number; recentBatches: unknown[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api<{ data: unknown[]; total: number }>("/api/products?limit=1"),
      api<{ data: unknown[] }>("/api/import/batches"),
    ])
      .then(([products, batches]) => {
        setStats({
          total: (products as { total?: number }).total ?? 0,
          recentBatches: (batches as { data?: unknown[] }).data ?? [],
        });
      })
      .catch(() => setStats({ total: 0, recentBatches: [] }))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">手机产品参数查询与竞品分析</h1>
        <p className="mt-1 text-gray-600">从 GSMArena 抓取机型、模板批量导入、批量更新价格、生成 AI 竞品报告。</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>总机型数</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <p className="text-gray-500">加载中…</p> : <p className="text-2xl font-semibold">{stats?.total ?? 0}</p>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>最近价格导入</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <p className="text-gray-500">加载中…</p> : <p className="text-sm text-gray-600">共 {stats?.recentBatches?.length ?? 0} 个批次</p>}
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold">快捷入口</h2>
        <div className="flex flex-wrap gap-3">
          <Link href="/gsmarena"><Button>查询 GSMArena 机型</Button></Link>
          <Link href="/products"><Button variant="outline">产品数据库</Button></Link>
          <Link href="/price"><Button variant="outline">批量更新价格</Button></Link>
          <Link href="/compare"><Button variant="outline">竞品分析</Button></Link>
          <Link href="/settings"><Button variant="ghost">系统设置</Button></Link>
        </div>
      </div>
    </div>
  );
}
