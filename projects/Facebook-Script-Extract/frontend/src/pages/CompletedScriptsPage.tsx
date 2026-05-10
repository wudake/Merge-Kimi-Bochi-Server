import { useEffect, useState } from 'react'
import { Loader2, RefreshCw, FileText, ExternalLink, Clock, Copy, Check } from 'lucide-react'
import { tasksApi, type TaskInfo, type TaskResult } from '../api/client'

interface ScriptItem {
  task: TaskInfo
  result: TaskResult | null
}

export default function CompletedScriptsPage() {
  const [items, setItems] = useState<ScriptItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copiedIds, setCopiedIds] = useState<Set<string>>(new Set())

  const handleCopy = async (taskId: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedIds((prev) => new Set(prev).add(taskId))
      setTimeout(() => {
        setCopiedIds((prev) => {
          const next = new Set(prev)
          next.delete(taskId)
          return next
        })
      }, 2000)
    } catch {
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopiedIds((prev) => new Set(prev).add(taskId))
      setTimeout(() => {
        setCopiedIds((prev) => {
          const next = new Set(prev)
          next.delete(taskId)
          return next
        })
      }, 2000)
    }
  }

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await tasksApi.list(0, 200)
      const completed = res.data.filter((t) => t.status === 'completed')

      const results = await Promise.all(
        completed.map(async (task) => {
          try {
            const r = await tasksApi.getResult(task.id)
            return { task, result: r.data }
          } catch {
            return { task, result: null }
          }
        })
      )

      results.sort((a, b) => {
        const aTime = a.task.completed_at ? new Date(a.task.completed_at).getTime() : 0
        const bTime = b.task.completed_at ? new Date(b.task.completed_at).getTime() : 0
        return bTime - aTime
      })
      setItems(results)
    } catch (err: any) {
      setError(err.response?.data?.detail || '获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FileText className="w-7 h-7 text-primary-600" />
          已完成视频脚本
        </h1>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>
      )}

      {loading && items.length === 0 && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      )}

      {!loading && items.length === 0 && (
        <div className="text-center py-20 text-gray-400 text-sm">
          暂无已完成的视频脚本
        </div>
      )}

      <div className="space-y-4">
        {items.map((item) => (
          <div
            key={item.task.id}
            className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
          >
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
              <ExternalLink className="w-3.5 h-3.5 text-gray-400 shrink-0" />
              <a
                href={item.task.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary-600 hover:underline truncate"
                title={item.task.url}
              >
                {item.task.url}
              </a>
              <div className="ml-auto flex items-center gap-3 shrink-0">
                {item.task.completed_at && (
                  <span className="flex items-center gap-1 text-xs text-gray-400">
                    <Clock className="w-3 h-3" />
                    {new Date(item.task.completed_at).toLocaleString('zh-CN')}
                  </span>
                )}
                {item.result?.duration && (
                  <span className="text-xs text-gray-400">
                    {item.result.duration.toFixed(1)}s
                  </span>
                )}
              </div>
            </div>
            <div className="px-5 py-4">
              {item.result?.full_text ? (
                (() => {
                  const text = item.result.full_text
                  return (
                    <div className="relative">
                      <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto scrollbar-thin pr-20">
                        {text}
                      </div>
                      <button
                        onClick={() => handleCopy(item.task.id, text)}
                        className="absolute top-0 right-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-gray-200 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors bg-white shadow-sm"
                      >
                        {copiedIds.has(item.task.id) ? <Check className="w-3 h-3 text-green-600" /> : <Copy className="w-3 h-3" />}
                        {copiedIds.has(item.task.id) ? '已复制' : '复制'}
                      </button>
                    </div>
                  )
                })()
              ) : (
                <div className="text-sm text-gray-400 italic">暂无脚本内容</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
