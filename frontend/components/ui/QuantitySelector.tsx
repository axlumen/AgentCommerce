/**
 * 数量选择器组件
 */

'use client';

import { Button } from '@/components/ui/button';
import { Minus, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuantitySelectorProps {
  quantity: number;
  onQuantityChange: (quantity: number) => void;
  min?: number;
  max?: number;
  /** 尺寸变体 */
  size?: 'sm' | 'md';
  className?: string;
}

export function QuantitySelector({
  quantity,
  onQuantityChange,
  min = 1,
  max,
  size = 'md',
  className,
}: QuantitySelectorProps) {
  const iconSize = size === 'sm' ? 'h-3 w-3' : 'h-4 w-4';
  const buttonSize = size === 'sm' ? 'h-8 w-8' : 'h-10 w-10';
  const textWidth = size === 'sm' ? 'w-10' : 'w-12';
  const textSize = size === 'sm' ? 'text-sm' : '';

  return (
    <div className={cn('flex items-center border rounded-lg', className)}>
      <Button
        variant="ghost"
        size="icon"
        className={buttonSize}
        onClick={() => onQuantityChange(Math.max(min, quantity - 1))}
        disabled={quantity <= min}
      >
        <Minus className={iconSize} />
      </Button>
      <span className={cn(textWidth, 'text-center font-medium', textSize)}>
        {quantity}
      </span>
      <Button
        variant="ghost"
        size="icon"
        className={buttonSize}
        onClick={() => onQuantityChange(max ? Math.min(max, quantity + 1) : quantity + 1)}
        disabled={max !== undefined && quantity >= max}
      >
        <Plus className={iconSize} />
      </Button>
    </div>
  );
}
