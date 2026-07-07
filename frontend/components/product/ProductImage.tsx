/**
 * 商品图片组件，无图时显示占位
 */

import { cn } from '@/lib/utils';

interface ProductImageProps {
  src?: string | null;
  alt: string;
  className?: string;
  fallbackClassName?: string;
}

export function ProductImage({ src, alt, className, fallbackClassName }: ProductImageProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={alt}
        className={cn('object-cover w-full h-full', className)}
      />
    );
  }

  return (
    <div
      className={cn(
        'w-full h-full flex items-center justify-center text-4xl',
        fallbackClassName
      )}
    >
      📦
    </div>
  );
}
