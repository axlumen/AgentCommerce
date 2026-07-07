/**
 * 订单列表页面
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ProductImage } from '@/components/product/ProductImage';
import { api, type Order } from '@/lib/api';
import { useRequireAuth } from '@/hooks/useAuth';
import { formatPrice, formatDate, getOrderStatusText, getOrderStatusColor } from '@/lib/utils';
import { Package, CreditCard, XCircle, CheckCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function OrdersPage() {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');

  const fetchOrders = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.orders.list();
      setOrders(data);
    } catch {
      toast.error('获取订单失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchOrders();
    }
  }, [isAuthenticated, fetchOrders]);

  const handleOrderAction = async (
    action: 'pay' | 'cancel' | 'confirm',
    orderId: number,
    successMessage: string
  ) => {
    try {
      await api.orders[action](orderId);
      toast.success(successMessage);
      fetchOrders();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '操作失败');
    }
  };

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

  const filteredOrders = activeTab === 'all'
    ? orders
    : orders.filter((order) => order.status === activeTab);

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">我的订单</h1>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="all">全部</TabsTrigger>
          <TabsTrigger value="pending">待支付</TabsTrigger>
          <TabsTrigger value="paid">已支付</TabsTrigger>
          <TabsTrigger value="shipped">已发货</TabsTrigger>
          <TabsTrigger value="completed">已完成</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab}>
          {isLoading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">加载中...</p>
            </div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-12">
              <Package className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h2 className="text-xl font-semibold mb-2">暂无订单</h2>
              <p className="text-muted-foreground mb-6">快去挑选心仪的商品吧</p>
              <Button asChild>
                <Link href="/products">浏览商品</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredOrders.map((order) => (
                <Card key={order.id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-muted-foreground">
                          订单号: {order.id}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {formatDate(order.created_at)}
                        </span>
                      </div>
                      <Badge className={getOrderStatusColor(order.status)}>
                        {getOrderStatusText(order.status)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* 订单商品 */}
                    <div className="space-y-3">
                      {order.items.map((item) => (
                        <div key={item.id} className="flex items-center gap-4">
                          <div className="w-16 h-16 bg-muted rounded-lg overflow-hidden flex-shrink-0">
                            <ProductImage src={item.product_image} alt={item.product_name} fallbackClassName="text-lg" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium line-clamp-1">
                              {item.product_name}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              x{item.quantity}
                            </p>
                          </div>
                          <p className="font-medium">{formatPrice(item.subtotal)}</p>
                        </div>
                      ))}
                    </div>

                    <Separator className="my-4" />

                    {/* 订单操作 */}
                    <div className="flex items-center justify-between">
                      <div className="text-lg font-bold">
                        合计: <span className="text-primary">{formatPrice(order.total_amount)}</span>
                      </div>
                      <div className="flex gap-2">
                        {order.status === 'pending' && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleOrderAction('cancel', order.id, '订单已取消')}
                            >
                              <XCircle className="mr-2 h-4 w-4" />
                              取消订单
                            </Button>
                            <Button size="sm" onClick={() => handleOrderAction('pay', order.id, '支付成功')}>
                              <CreditCard className="mr-2 h-4 w-4" />
                              立即支付
                            </Button>
                          </>
                        )}
                        {order.status === 'shipped' && (
                          <Button size="sm" onClick={() => handleOrderAction('confirm', order.id, '已确认收货')}>
                            <CheckCircle className="mr-2 h-4 w-4" />
                            确认收货
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
