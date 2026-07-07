'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import { useAuthStore } from '@/store/auth';

export function HeroActions() {
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="flex gap-4">
      <Button asChild>
        <Link href="/products">
          浏览商品
          <ArrowRight className="ml-2 h-4 w-4" />
        </Link>
      </Button>
      {!isAuthenticated && (
        <Button variant="outline" asChild>
          <Link href="/login">立即登录</Link>
        </Button>
      )}
    </div>
  );
}
