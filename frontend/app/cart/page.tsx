/**
 * 购物车页面
 */

'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { QuantitySelector } from '@/components/ui/QuantitySelector';
import { ProductImage } from '@/components/product/ProductImage';
import { useCartStore } from '@/store/cart';
import { useRequireAuth } from '@/hooks/useAuth';
import { formatPrice } from '@/lib/utils';
import { Trash2, ShoppingCart, ArrowLeft } from 'lucide-react';

export default function CartPage() {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const { items, isLoading, totalAmount, totalItems, fetchCart, updateQuantity, removeItem, clearCart } =
    useCartStore();

  useEffect(() => {
    if (isAuthenticated) {
      fetchCart();
    }
  }, [isAuthenticated, fetchCart]);

  if (authLoading || !isAuthenticated) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <div className="text-center py-12">
          <p className="text-muted-foreground">加载中...</p>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <div className="text-center py-12">
          <ShoppingCart className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h2 className="text-xl font-semibold mb-2">购物车为空</h2>
          <p className="text-muted-foreground mb-6">快去挑选心仪的商品吧</p>
          <Button asChild>
            <Link href="/products">浏览商品</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">购物车</h1>
        <Button variant="ghost" asChild>
          <Link href="/products">
            <ArrowLeft className="mr-2 h-4 w-4" />
            继续购物
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 购物车列表 */}
        <div className="lg:col-span-2 space-y-4">
          {items.map((item) => (
            <Card key={item.product_id}>
              <CardContent className="p-4">
                <div className="flex gap-4">
                  {/* 商品图片 */}
                  <div className="w-24 h-24 bg-muted rounded-lg overflow-hidden flex-shrink-0">
                    <ProductImage src={item.product_image} alt={item.product_name} fallbackClassName="text-2xl" />
                  </div>

                  {/* 商品信息 */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium line-clamp-2">
                      <Link
                        href={`/products/${item.product_id}`}
                        className="hover:text-primary"
                      >
                        {item.product_name}
                      </Link>
                    </h3>
                    <p className="text-lg font-bold text-primary mt-2">
                      {formatPrice(item.product_price)}
                    </p>
                  </div>

                  {/* 数量操作 */}
                  <div className="flex flex-col items-end gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => removeItem(item.product_id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                    <QuantitySelector
                      size="sm"
                      quantity={item.quantity}
                      onQuantityChange={(qty) => updateQuantity(item.product_id, qty)}
                    />
                    <p className="text-sm font-medium">
                      {formatPrice(item.product_price * item.quantity)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* 清空购物车 */}
          <div className="flex justify-end">
            <Button variant="ghost" size="sm" onClick={clearCart}>
              <Trash2 className="mr-2 h-4 w-4" />
              清空购物车
            </Button>
          </div>
        </div>

        {/* 订单汇总 */}
        <div>
          <Card className="sticky top-24">
            <CardHeader>
              <CardTitle>订单汇总</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">
                  商品 ({totalItems} 件)
                </span>
                <span>{formatPrice(totalAmount)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">运费</span>
                <span className="text-green-600">免费</span>
              </div>
              <Separator />
              <div className="flex justify-between text-lg font-bold">
                <span>合计</span>
                <span className="text-primary">{formatPrice(totalAmount)}</span>
              </div>
            </CardContent>
            <CardFooter>
              <Button className="w-full" size="lg" asChild>
                <Link href="/orders/create">去结算</Link>
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
}
