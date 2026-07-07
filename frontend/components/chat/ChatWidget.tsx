/**
 * AI 聊天悬浮窗组件
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageCircle, X, Send, Bot, User, Loader2 } from 'lucide-react';
import { useUIStore } from '@/store/ui';
import { useAuthStore } from '@/store/auth';
import { api, type ChatResponse } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ChatResponse['tool_calls'];
  timestamp: Date;
  toolStatus?: string;
}

export function ChatWidget() {
  const { chatOpen, setChatOpen } = useUIStore();
  const { isAuthenticated } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    if (!isAuthenticated) {
      toast.error('请先登录');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // 预创建 assistant 消息用于流式更新
    const assistantId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      await api.agent.chatStream(
        {
          message: userMessage.content,
          session_id: sessionId || undefined,
        },
        {
          onToken: (content) => {
            setIsLoading(false);
            setIsStreaming(true);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantId
                  ? { ...msg, content: msg.content + content }
                  : msg
              )
            );
          },
          onToolStart: (name) => {
            const toolLabel = {
              search_products: '正在搜索商品...',
              get_product_detail: '正在查询商品详情...',
              check_stock: '正在检查库存...',
              calculate_final_price: '正在计算价格...',
              add_to_cart: '正在添加到购物车...',
              get_user_preferences: '正在读取偏好...',
              compare_products: '正在对比商品...',
            }[name] || `正在调用 ${name}...`;

            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantId
                  ? { ...msg, toolStatus: toolLabel }
                  : msg
              )
            );
          },
          onToolEnd: () => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantId
                  ? { ...msg, toolStatus: undefined }
                  : msg
              )
            );
          },
          onDone: (data) => {
            if (!sessionId) {
              setSessionId(data.session_id);
            }
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantId
                  ? {
                      ...msg,
                      content: data.reply || msg.content,
                      toolCalls: data.tool_calls,
                      toolStatus: undefined,
                    }
                  : msg
              )
            );
          },
          onNeedsConfirm: (data) => {
            setMessages((prev) => {
              const withoutEmpty = prev.filter(
                (msg) => msg.id !== assistantId || msg.content
              );
              return [
                ...withoutEmpty,
                {
                  id: (Date.now() + 2).toString(),
                  role: 'assistant' as const,
                  content: data.confirm_message || '需要您的确认',
                  timestamp: new Date(),
                },
              ];
            });
          },
          onError: (message) => {
            toast.error(message);
            // 移除空的 assistant 消息
            setMessages((prev) =>
              prev.filter(
                (msg) => msg.id !== assistantId || msg.content
              )
            );
          },
        }
      );
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '发送失败');
      setMessages((prev) =>
        prev.filter((msg) => msg.id !== assistantId || msg.content)
      );
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  if (!chatOpen) {
    return (
      <Button
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg"
        size="icon"
        onClick={() => setChatOpen(true)}
      >
        <MessageCircle className="h-6 w-6" />
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-6 right-6 w-[380px] h-[500px] shadow-xl flex flex-col z-50">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          AI 智能导购
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={clearChat}>
            清空
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setChatOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full p-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
              <Bot className="h-12 w-12 mb-4" />
              <p className="font-medium">你好！我是 AI 智能导购</p>
              <p className="text-sm mt-1">有什么可以帮你的吗？</p>
              <div className="grid grid-cols-2 gap-2 mt-4 w-full">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => setInput('推荐一些热销手机')}
                >
                  推荐手机
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => setInput('有什么优惠活动？')}
                >
                  优惠活动
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => setInput('帮我找一款笔记本电脑')}
                >
                  找笔记本
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => setInput('查看我的购物车')}
                >
                  购物车
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    'flex gap-2',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}
                  <div
                    className={cn(
                      'max-w-[80%] rounded-lg px-3 py-2 text-sm',
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    )}
                  >
                    {/* 思考中状态 */}
                    {msg.role === 'assistant' &&
                      !msg.content &&
                      isLoading &&
                      msg.id === messages[messages.length - 1]?.id && (
                        <div className="flex items-center gap-1.5 text-muted-foreground">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span>思考中...</span>
                        </div>
                      )}
                    {/* 消息内容：助手用 Markdown 渲染，用户用纯文本 */}
                    {msg.role === 'assistant' ? (
                      <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                        <Markdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                            li: ({ children }) => <li className="mb-0.5">{children}</li>,
                            code: ({ children, className }) => {
                              const isInline = !className;
                              return isInline ? (
                                <code className="bg-muted-foreground/20 px-1 py-0.5 rounded text-xs">{children}</code>
                              ) : (
                                <code className={className}>{children}</code>
                              );
                            },
                            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                            table: ({ children }) => (
                              <div className="overflow-x-auto my-2">
                                <table className="w-full text-xs border-collapse">{children}</table>
                              </div>
                            ),
                            thead: ({ children }) => <thead className="bg-muted/50">{children}</thead>,
                            tbody: ({ children }) => <tbody>{children}</tbody>,
                            tr: ({ children }) => <tr className="border-b border-border last:border-0">{children}</tr>,
                            th: ({ children }) => (
                              <th className="px-2 py-1.5 text-left font-semibold whitespace-nowrap">{children}</th>
                            ),
                            td: ({ children }) => (
                              <td className="px-2 py-1.5 whitespace-nowrap">{children}</td>
                            ),
                          }}
                        >
                          {msg.content}
                        </Markdown>
                      </div>
                    ) : (
                      msg.content
                    )}
                    {/* 流式光标 */}
                    {isStreaming &&
                      msg.role === 'assistant' &&
                      msg.id === messages[messages.length - 1]?.id && (
                        <span className="inline-block w-0.5 h-4 bg-foreground animate-pulse ml-0.5 align-text-bottom" />
                      )}
                    {/* 工具状态提示 */}
                    {msg.toolStatus && (
                      <div className="flex items-center gap-1.5 mt-1.5 text-xs text-muted-foreground">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        {msg.toolStatus}
                      </div>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-primary-foreground" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>
      </CardContent>

      <CardFooter className="p-3 pt-0">
        <div className="flex w-full gap-2">
          <Input
            placeholder="输入消息..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
