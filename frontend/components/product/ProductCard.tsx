/**
 * 商品卡片组件
 */

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ProductImage } from '@/components/product/ProductImage';
import { type Product } from '@/lib/api';
import { formatPrice } from '@/lib/utils';
import { ShoppingCart } from 'lucide-react';

interface ProductCardProps {
  product: Product;
  /** 是否显示缺货标签，默认 false */
  showStockBadge?: boolean;
}

export function ProductCard({ product, showStockBadge = false }: ProductCardProps) {
  const isOutOfStock = product.stock <= 0;

  return (
    <Card className="group overflow-hidden transition-all hover:shadow-lg">
      <div className="aspect-square bg-muted relative overflow-hidden">
        <ProductImage
          src={product.image_url}
          alt={product.name}
          className="transition-transform group-hover:scale-105"
        />
        {product.brand && (
          <Badge variant="secondary" className="absolute top-2 left-2">
            {product.brand}
          </Badge>
        )}
        {showStockBadge && isOutOfStock && (
          <Badge variant="destructive" className="absolute top-2 right-2">
            缺货
          </Badge>
        )}
      </div>
      <CardHeader className="p-3">
        <CardTitle className="text-sm line-clamp-2">
          <Link href={`/products/${product.id}`} className="hover:text-primary">
            {product.name}
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 pt-0">
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-primary">
            {formatPrice(product.price)}
          </span>
          <span className="text-xs text-muted-foreground">
            已售 {product.sales_count}
          </span>
        </div>
      </CardContent>
      <CardFooter className="p-3 pt-0">
        <Button asChild className="w-full" size="sm" disabled={showStockBadge && isOutOfStock}>
          <Link href={`/products/${product.id}`}>
            <ShoppingCart className="mr-2 h-4 w-4" />
            {showStockBadge && isOutOfStock ? '暂时缺货' : '查看详情'}
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
