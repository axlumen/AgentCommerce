/**
 * 结算页面
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ProductImage } from '@/components/product/ProductImage';
import { useCartStore } from '@/store/cart';
import { useRequireAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';
import { formatPrice } from '@/lib/utils';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function CheckoutPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const { items, totalAmount, totalItems, fetchCart } = useCartStore();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [form, setForm] = useState({
    receiver_name: '',
    phone: '',
    address: '',
    remark: '',
  });

  useEffect(() => {
    if (isAuthenticated) {
      fetchCart();
    }
  }, [isAuthenticated, fetchCart]);

  if (authLoading) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (items.length === 0) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">购物车为空，无法结算</p>
          <Button asChild>
            <Link href="/products">浏览商品</Link>
          </Button>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.receiver_name.trim()) {
      toast.error('请输入收货人姓名');
      return;
    }
    if (!form.phone.trim()) {
      toast.error('请输入手机号');
      return;
    }
    if (!form.address.trim()) {
      toast.error('请输入收货地址');
      return;
    }

    setIsSubmitting(true);
    try {
      const order = await api.orders.create({
        cart_item_ids: items.map((item) => item.product_id),
        address: {
          name: form.receiver_name,
          phone: form.phone,
          address: form.address,
        },
        remark: form.remark || undefined,
      });
      toast.success('订单创建成功');
      router.push('/orders');
    } catch (error: any) {
      toast.error(error.message || '创建订单失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">确认订单</h1>
        <Button variant="ghost" asChild>
          <Link href="/cart">
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回购物车
          </Link>
        </Button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：商品列表 + 地址表单 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 商品列表 */}
            <Card>
              <CardHeader>
                <CardTitle>商品信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {items.map((item) => (
                  <div key={item.product_id} className="flex gap-4">
                    <div className="w-16 h-16 bg-muted rounded-lg overflow-hidden flex-shrink-0">
                      <ProductImage src={item.product_image} alt={item.product_name} fallbackClassName="text-lg" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium line-clamp-1">{item.product_name}</p>
                      <p className="text-sm text-muted-foreground">× {item.quantity}</p>
                    </div>
                    <p className="font-medium">{formatPrice(item.product_price * item.quantity)}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* 收货信息 */}
            <Card>
              <CardHeader>
                <CardTitle>收货信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="receiver_name">收货人 *</Label>
                    <Input
                      id="receiver_name"
                      placeholder="请输入收货人姓名"
                      value={form.receiver_name}
                      onChange={(e) => updateField('receiver_name', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">手机号 *</Label>
                    <Input
                      id="phone"
                      placeholder="请输入手机号"
                      value={form.phone}
                      onChange={(e) => updateField('phone', e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">收货地址 *</Label>
                  <Textarea
                    id="address"
                    placeholder="请输入详细收货地址"
                    rows={3}
                    value={form.address}
                    onChange={(e) => updateField('address', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="remark">备注</Label>
                  <Input
                    id="remark"
                    placeholder="选填，如有特殊要求请备注"
                    value={form.remark}
                    onChange={(e) => updateField('remark', e.target.value)}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 右侧：订单汇总 */}
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
                <Button type="submit" className="w-full" size="lg" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      提交中...
                    </>
                  ) : (
                    '提交订单'
                  )}
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}
