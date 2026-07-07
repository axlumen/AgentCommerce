/**
 * 工具函数
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 合并 Tailwind 类名
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 格式化价格
 */
export function formatPrice(price: number | string): string {
  const num = typeof price === 'string' ? parseFloat(price) : price;
  return `¥${num.toFixed(2)}`;
}

/**
 * 格式化日期
 */
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 订单状态映射
 */
const ORDER_STATUS_MAP: Record<string, { text: string; color: string }> = {
  pending: { text: '待支付', color: 'bg-yellow-100 text-yellow-800' },
  paid: { text: '已支付', color: 'bg-blue-100 text-blue-800' },
  shipped: { text: '已发货', color: 'bg-purple-100 text-purple-800' },
  completed: { text: '已完成', color: 'bg-green-100 text-green-800' },
  cancelled: { text: '已取消', color: 'bg-gray-100 text-gray-800' },
};

export function getOrderStatusText(status: string): string {
  return ORDER_STATUS_MAP[status]?.text || status;
}

export function getOrderStatusColor(status: string): string {
  return ORDER_STATUS_MAP[status]?.color || 'bg-gray-100 text-gray-800';
}

/**
 * 截断文本
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}
