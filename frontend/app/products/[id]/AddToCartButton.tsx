/**
 * 加入购物车按钮组件
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { QuantitySelector } from '@/components/ui/QuantitySelector';
import { ShoppingCart } from 'lucide-react';
import { useCartStore } from '@/store/cart';
import { useAuthStore } from '@/store/auth';
import { type Product } from '@/lib/api';

interface AddToCartButtonProps {
  product: Product;
}

export function AddToCartButton({ product }: AddToCartButtonProps) {
  const [quantity, setQuantity] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const { addItem } = useCartStore();
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    setIsLoading(true);
    try {
      await addItem({ product_id: product.id, quantity });
      setQuantity(1);
    } catch {
      // 错误已在 store 中处理
    } finally {
      setIsLoading(false);
    }
  };

  const isDisabled = product.stock <= 0 || isLoading;

  return (
    <div className="space-y-4">
      {/* 数量选择 */}
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium">数量</span>
        <QuantitySelector
          quantity={quantity}
          onQuantityChange={setQuantity}
          max={product.stock}
        />
      </div>

      {/* 加入购物车按钮 */}
      <Button
        className="w-full"
        size="lg"
        onClick={handleAddToCart}
        disabled={isDisabled}
      >
        <ShoppingCart className="mr-2 h-5 w-5" />
        {isLoading ? '添加中...' : product.stock > 0 ? '加入购物车' : '暂时缺货'}
      </Button>
    </div>
  );
}
