/**
 * 首页
 */

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ProductCard } from '@/components/product/ProductCard';
import { HeroActions } from '@/components/HeroActions';
import { api, type ProductParams } from '@/lib/api';
import { Sparkles, ArrowRight } from 'lucide-react';

// ISR: 每 60 秒重新生成
export const revalidate = 60;

async function getProducts(params: ProductParams) {
  try {
    const data = await api.products.list(params);
    return data.items;
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const [hotProducts, newProducts] = await Promise.all([
    getProducts({ page: 1, size: 8, sort_by: 'sales_count', sort_order: 'desc' }),
    getProducts({ page: 1, size: 4, sort_by: 'created_at', sort_order: 'desc' }),
  ]);

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      {/* Hero 区域 */}
      <section className="mb-12">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary/10 via-primary/5 to-background p-8 md:p-12">
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-primary" />
              <span className="text-sm font-medium text-primary">
                AI 智能导购
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4">
              欢迎来到 AgentCommerce
            </h1>
            <p className="text-muted-foreground mb-6 max-w-lg">
              基于 AI 的智能导购电商平台，支持语义搜索、智能推荐、多轮对话
            </p>
            <div className="flex gap-4">
              <HeroActions />
            </div>
          </div>
        </div>
      </section>

      {/* 热销商品 */}
      <section className="mb-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">🔥 热销商品</h2>
          <Button variant="ghost" asChild>
            <Link href="/products?sort_by=sales_count">
              查看更多
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {hotProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* 新品上架 */}
      <section className="mb-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">✨ 新品上架</h2>
          <Button variant="ghost" asChild>
            <Link href="/products?sort_by=created_at">
              查看更多
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
          {newProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* 特性介绍 */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-center mb-8">平台特色</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">🤖</span>
                AI 智能导购
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                基于 LangGraph 的 ReAct Agent，支持多轮对话、自动搜索、比价、库存校验
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">🔍</span>
                三级混合检索
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                BM25 关键词 + FAISS 向量 + Cross-Encoder Reranker，精准匹配商品
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">⚡</span>
                语义缓存
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Redis 存储 query embedding，相似度 ≥ 0.9 直接返回，延迟 {'<'}10ms
              </p>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
