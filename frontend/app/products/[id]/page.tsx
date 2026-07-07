/**
 * 商品详情页
 */

import { notFound } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { api, type Product } from '@/lib/api';
import { formatPrice } from '@/lib/utils';
import { ShoppingCart, ArrowLeft, Package, Truck, Shield } from 'lucide-react';
import Link from 'next/link';
import { AddToCartButton } from './AddToCartButton';

// ISR: 每 60 秒重新生成
export const revalidate = 60;

interface ProductDetailPageProps {
  params: Promise<{
    id: string;
  }>;
}

async function getProduct(id: number): Promise<Product | null> {
  try {
    return await api.products.detail(id);
  } catch {
    return null;
  }
}

export default async function ProductDetailPage({ params }: ProductDetailPageProps) {
  const { id } = await params;
  const product = await getProduct(Number(id));

  if (!product) {
    notFound();
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      {/* 返回按钮 */}
      <Button variant="ghost" asChild className="mb-6">
        <Link href="/products">
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回商品列表
        </Link>
      </Button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* 商品图片 */}
        <div className="aspect-square bg-muted rounded-lg overflow-hidden">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-6xl">
              📦
            </div>
          )}
        </div>

        {/* 商品信息 */}
        <div className="space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              {product.brand && <Badge variant="secondary">{product.brand}</Badge>}
              {product.stock <= 0 && <Badge variant="destructive">缺货</Badge>}
            </div>
            <h1 className="text-3xl font-bold">{product.name}</h1>
          </div>

          <div className="flex items-baseline gap-4">
            <span className="text-3xl font-bold text-primary">
              {formatPrice(product.price)}
            </span>
            <span className="text-sm text-muted-foreground">
              已售 {product.sales_count} 件
            </span>
          </div>

          <Separator />

          {/* 商品描述 */}
          {product.description && (
            <div>
              <h3 className="font-medium mb-2">商品描述</h3>
              <p className="text-muted-foreground">{product.description}</p>
            </div>
          )}

          {/* 规格参数 */}
          {product.specs && Object.keys(product.specs).length > 0 && (
            <div>
              <h3 className="font-medium mb-2">规格参数</h3>
              <Card>
                <CardContent className="p-4">
                  <dl className="grid grid-cols-2 gap-2">
                    {Object.entries(product.specs).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <dt className="text-muted-foreground">{key}</dt>
                        <dd className="font-medium">{String(value)}</dd>
                      </div>
                    ))}
                  </dl>
                </CardContent>
              </Card>
            </div>
          )}

          <Separator />

          {/* 库存信息 */}
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">
              {product.stock > 0 ? `库存 ${product.stock} 件` : '暂时缺货'}
            </span>
          </div>

          {/* 操作按钮 */}
          <AddToCartButton product={product} />

          {/* 服务保障 */}
          <div className="grid grid-cols-3 gap-4 pt-4">
            <div className="flex flex-col items-center gap-2 text-center">
              <Truck className="h-5 w-5 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">免费配送</span>
            </div>
            <div className="flex flex-col items-center gap-2 text-center">
              <Shield className="h-5 w-5 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">正品保障</span>
            </div>
            <div className="flex flex-col items-center gap-2 text-center">
              <Package className="h-5 w-5 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">7天退换</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
