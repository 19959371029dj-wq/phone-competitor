import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "手机产品参数与竞品分析",
  description: "GSMArena 查询、Profile 导入、价格批量更新、AI 竞品分析",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen antialiased">
        <header className="border-b bg-white/80">
          <div className="container mx-auto flex h-14 items-center px-4">
            <Link href="/" className="font-semibold text-lg">手机竞品分析</Link>
            <nav className="ml-8 flex gap-6">
              <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">首页</Link>
              <Link href="/gsmarena" className="text-sm text-gray-600 hover:text-gray-900">GSMArena 查询</Link>
              <Link href="/products" className="text-sm text-gray-600 hover:text-gray-900">产品数据库</Link>
              <Link href="/price" className="text-sm text-gray-600 hover:text-gray-900">价格批量更新</Link>
              <Link href="/compare" className="text-sm text-gray-600 hover:text-gray-900">竞品分析</Link>
              <Link href="/settings" className="text-sm text-gray-600 hover:text-gray-900">设置</Link>
            </nav>
          </div>
        </header>
        <main className="container mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
