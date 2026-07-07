/**
 * 商品列表页
 */

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ProductCard } from '@/components/product/ProductCard';
import { api, type ProductParams } from '@/lib/api';
import { Search } from 'lucide-react';

// ISR: 每 60 秒重新生成
export const revalidate = 60;

interface ProductsPageProps {
  searchParams: Promise<{
    page?: string;
    sort_by?: string;
    sort_order?: string;
    keyword?: string;
  }>;
}

async function getProducts(params: ProductParams) {
  try {
    return await api.products.list(params);
  } catch {
    return { items: [], total: 0, page: 1, size: 12, pages: 0 };
  }
}

export default async function ProductsPage({ searchParams }: ProductsPageProps) {
  const params = await searchParams;
  const page = Number(params.page) || 1;
  const sortBy = params.sort_by || 'sales_count';
  const sortOrder = params.sort_order || 'desc';
  const keyword = params.keyword || '';

  const { items, total, pages } = await getProducts({
    page,
    size: 12,
    sort_by: sortBy,
    sort_order: sortOrder,
    keyword: keyword || undefined,
  });

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">商品列表</h1>
        <p className="text-muted-foreground">
          共 {total} 件商品
        </p>
      </div>

      {/* 搜索和排序 */}
      <div className="flex flex-col sm:flex-row gap-4 mb-8">
        <form className="flex-1 relative" action="/products" method="get">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            name="keyword"
            placeholder="搜索商品..."
            defaultValue={keyword}
            className="pl-10"
          />
          <input type="hidden" name="sort_by" value={sortBy} />
          <input type="hidden" name="sort_order" value={sortOrder} />
        </form>
        <div className="flex gap-2">
          <Button
            variant={sortBy === 'sales_count' ? 'default' : 'outline'}
            size="sm"
            asChild
          >
            <Link href={`/products?sort_by=sales_count&sort_order=desc${keyword ? `&keyword=${keyword}` : ''}`}>
              销量
            </Link>
          </Button>
          <Button
            variant={sortBy === 'price' ? 'default' : 'outline'}
            size="sm"
            asChild
          >
            <Link href={`/products?sort_by=price&sort_order=${sortBy === 'price' && sortOrder === 'asc' ? 'desc' : 'asc'}${keyword ? `&keyword=${keyword}` : ''}`}>
              价格 {sortBy === 'price' && (sortOrder === 'asc' ? '↑' : '↓')}
            </Link>
          </Button>
          <Button
            variant={sortBy === 'created_at' ? 'default' : 'outline'}
            size="sm"
            asChild
          >
            <Link href={`/products?sort_by=created_at&sort_order=desc${keyword ? `&keyword=${keyword}` : ''}`}>
              最新
            </Link>
          </Button>
        </div>
      </div>

      {/* 商品网格 */}
      {items.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {items.map((product) => (
            <ProductCard key={product.id} product={product} showStockBadge />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-muted-foreground">暂无商品</p>
        </div>
      )}

      {/* 分页 */}
      {pages > 1 && (
        <div className="flex justify-center gap-2 mt-8">
          {page > 1 && (
            <Button variant="outline" asChild>
              <Link
                href={`/products?page=${page - 1}&sort_by=${sortBy}&sort_order=${sortOrder}${keyword ? `&keyword=${keyword}` : ''}`}
              >
                上一页
              </Link>
            </Button>
          )}
          <span className="flex items-center px-4 text-sm text-muted-foreground">
            {page} / {pages}
          </span>
          {page < pages && (
            <Button variant="outline" asChild>
              <Link
                href={`/products?page=${page + 1}&sort_by=${sortBy}&sort_order=${sortOrder}${keyword ? `&keyword=${keyword}` : ''}`}
              >
                下一页
              </Link>
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
