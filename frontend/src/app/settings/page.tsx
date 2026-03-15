"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  const [settings, setSettings] = useState<{ default_currency?: string; default_market_region?: string; gsmarena_timeout_seconds?: number; deepseek_configured?: boolean } | null>(null);

  useEffect(() => {
    api<{ data: unknown }>("/api/settings")
      .then((res) => setSettings((res as { data?: typeof settings }).data || null))
      .catch(() => setSettings(null));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">系统设置</h1>
        <p className="mt-1 text-gray-600">API Key 与敏感配置请在项目 .env 中设置，本页仅展示当前生效项。</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>当前配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {settings ? (
            <>
              <p><strong>默认币种：</strong>{settings.default_currency ?? "-"}</p>
              <p><strong>默认市场区域：</strong>{settings.default_market_region ?? "-"}</p>
              <p><strong>抓取超时（秒）：</strong>{settings.gsmarena_timeout_seconds ?? "-"}</p>
              <p><strong>DeepSeek API：</strong>{settings.deepseek_configured ? "已配置" : "未配置（请在 .env 设置 DEEPSEEK_API_KEY）"}</p>
            </>
          ) : (
            <p className="text-gray-500">加载中…</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>环境变量说明</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-gray-600 space-y-1">
          <p>DEEPSEEK_API_KEY — DeepSeek API Key，用于竞品分析报告</p>
          <p>DEEPSEEK_BASE_URL — 可选，默认 https://api.deepseek.com</p>
          <p>DATABASE_URL — 可选，默认 SQLite：./data/phone_competitor.db</p>
        </CardContent>
      </Card>
    </div>
  );
}
