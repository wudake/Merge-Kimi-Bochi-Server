import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Download, Loader2, AlertCircle, CheckCircle2, Copy, Check, Film } from 'lucide-react'
import { tasksApi, type TaskInfo, type TaskResult } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'

const statusMap: Record<string, { label: string; color: string }> = {
  pending: { label: '等待中', color: 'text-gray-500' },
  downloading: { label: '下载中', color: 'text-blue-600' },
  extracting_audio: { label: '提取音频', color: 'text-purple-600' },
  transcribing: { label: '识别中', color: 'text-amber-600' },
  completed: { label: '完成', color: 'text-green-600' },
  failed: { label: '失败', color: 'text-red-600' },
}

export default function TaskDetailPage() {
  const { taskId } = useParams()
  const [task, setTask] = useState<TaskInfo | null>(null)
  const [result, setResult] = useState<TaskResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const fetchData = async () => {
    if (!taskId) return
    setLoading(true)
    try {
      const [tRes, rRes] = await Promise.all([
        tasksApi.get(taskId),
        tasksApi.getResult(taskId).catch(() => null),
      ])
      setTask(tRes.data)
      if (rRes) setResult(rRes.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || '获取任务失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 3000)
    return () => clearInterval(interval)
  }, [taskId])

  useWebSocket((msg) => {
    if (msg.task_id === taskId) {
      setTask((prev) => prev ? { ...prev, progress: msg.progress ?? prev.progress, status: (msg.status as any) ?? prev.status } : prev)
    }
  })

  if (loading && !task) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    )
  }

  if (error || !task) {
    return (
      <div className="text-center py-20">
        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
        <p className="text-red-600">{error || '任务不存在'}</p>
        <Link to="/tasks" className="text-primary-600 hover:underline text-sm mt-4 inline-block">
          返回任务列表
        </Link>
      </div>
    )
  }

  const s = statusMap[task.status] || statusMap.pending

  return (
    <div className="max-w-3xl mx-auto">
      <Link to="/tasks" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft className="w-4 h-4" />
        返回列表
      </Link>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900 mb-1">任务详情</h1>
            <p className="text-sm text-gray-400 font-mono">{task.id}</p>
          </div>
          <span className={`text-sm font-semibold ${s.color}`}>{s.label}</span>
        </div>

        {/* 进度条 */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>处理进度</span>
            <span>{task.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div className="bg-primary-500 h-2.5 rounded-full transition-all duration-500" style={{ width: `${task.progress}%` }} />
          </div>
        </div>

        {/* 基本信息 */}
        <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
          <div className="bg-gray-50 rounded-lg p-3">
            <span className="text-gray-500 block mb-1">视频链接</span>
            <a href={task.url} target="_blank" className="text-primary-600 hover:underline truncate block">{task.url}</a>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <span className="text-gray-500 block mb-1">语言 / 格式</span>
            <span className="text-gray-700">{task.language} / {task.output_format.toUpperCase()}</span>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <span className="text-gray-500 block mb-1">引擎</span>
            <span className="text-gray-700">{task.use_local ? `本地 (${task.model_size})` : 'OpenAI API'}</span>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <span className="text-gray-500 block mb-1">创建时间</span>
            <span className="text-gray-700">{new Date(task.created_at).toLocaleString('zh-CN')}</span>
          </div>
        </div>

        {task.error_message && (
          <div className="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3 mb-6">
            <AlertCircle className="w-4 h-4 inline mr-1" />
            {task.error_message}
          </div>
        )}

        {task.status === 'completed' && (
          <div className="flex items-center gap-3 flex-wrap">
            <CheckCircle2 className="w-5 h-5 text-green-500" />
            <span className="text-green-700 text-sm font-medium">处理完成</span>
            {result?.duration && (
              <span className="text-gray-500 text-sm">时长: {result.duration.toFixed(1)}s</span>
            )}
            <div className="ml-auto flex items-center gap-2">
              {result?.video_url && (
                <a
                  href={tasksApi.downloadVideo(task.id)}
                  target="_blank"
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  <Film className="w-4 h-4" />
                  下载视频
                </a>
              )}
              <a
                href={tasksApi.download(task.id)}
                target="_blank"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                下载结果
              </a>
            </div>
          </div>
        )}

        {/* 预览 */}
        {result?.full_text && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-700">文本预览</h3>
              <button
                onClick={() => handleCopy(result.full_text!)}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-gray-200 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
              >
                {copied ? <Check className="w-3 h-3 text-green-600" /> : <Copy className="w-3 h-3" />}
                {copied ? '已复制' : '复制全文'}
              </button>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 max-h-96 overflow-y-auto scrollbar-thin whitespace-pre-wrap">
              {result.full_text}
            </div>
          </div>
        )}

        {result?.segments && result.segments.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">分段预览</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin">
              {result.segments.map((seg) => (
                <div key={seg.id} className="bg-gray-50 rounded-lg p-3 text-sm">
                  <span className="text-xs text-gray-400 font-mono">
                    [{seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s]
                  </span>
                  <p className="text-gray-700 mt-1">{seg.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
