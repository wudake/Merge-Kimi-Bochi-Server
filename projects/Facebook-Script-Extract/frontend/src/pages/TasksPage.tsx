import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, RefreshCw, Clock, Download, Film, AlertCircle, CheckCircle2, Trash2 } from 'lucide-react'
import { tasksApi, type TaskInfo } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'

const statusMap: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: '等待中', color: 'text-gray-500 bg-gray-100', icon: <Clock className="w-3.5 h-3.5" /> },
  downloading: { label: '下载中', color: 'text-blue-600 bg-blue-50', icon: <Loader2 className="w-3.5 h-3.5 animate-spin" /> },
  extracting_audio: { label: '提取音频', color: 'text-purple-600 bg-purple-50', icon: <Loader2 className="w-3.5 h-3.5 animate-spin" /> },
  transcribing: { label: '识别中', color: 'text-amber-600 bg-amber-50', icon: <Loader2 className="w-3.5 h-3.5 animate-spin" /> },
  completed: { label: '完成', color: 'text-green-600 bg-green-50', icon: <CheckCircle2 className="w-3.5 h-3.5" /> },
  failed: { label: '失败', color: 'text-red-600 bg-red-50', icon: <AlertCircle className="w-3.5 h-3.5" /> },
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchTasks = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await tasksApi.list(0, 50)
      setTasks(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || '获取任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
    const interval = setInterval(fetchTasks, 5000)
    return () => clearInterval(interval)
  }, [])

  useWebSocket((msg) => {
    if (msg.type === 'progress' || msg.type === 'status') {
      setTasks((prev) =>
        prev.map((t) =>
          t.id === msg.task_id
            ? { ...t, progress: msg.progress ?? t.progress, status: (msg.status as any) ?? t.status }
            : t
        )
      )
    }
  })

  const handleDelete = async (taskId: string) => {
    if (!confirm('确定要删除这个任务吗？相关文件也会被删除。')) return
    try {
      await tasksApi.delete(taskId)
      setTasks((prev) => prev.filter((t) => t.id !== taskId))
    } catch (err: any) {
      setError(err.response?.data?.detail || '删除任务失败')
    }
  }

  const handleClearAll = async () => {
    if (!confirm('确定要清空所有任务吗？所有任务数据和文件都会被删除，此操作不可恢复。')) return
    try {
      await tasksApi.clearAll()
      setTasks([])
    } catch (err: any) {
      setError(err.response?.data?.detail || '清空任务失败')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">任务列表</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={handleClearAll}
            disabled={loading || tasks.length === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-300 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Trash2 className="w-3.5 h-3.5" />
            清空全部
          </button>
          <button
            onClick={fetchTasks}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">状态</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">链接</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">格式</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">进度</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">创建时间</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {tasks.length === 0 && !loading && (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                  暂无任务，去 <Link to="/" className="text-primary-600 hover:underline">新建任务</Link>
                </td>
              </tr>
            )}
            {tasks.map((task) => {
              const s = statusMap[task.status] || statusMap.pending
              return (
                <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${s.color}`}>
                      {s.icon}
                      {s.label}
                    </span>
                  </td>
                  <td className="px-4 py-3 max-w-xs truncate text-gray-700">{task.url}</td>
                  <td className="px-4 py-3 text-gray-500 uppercase">{task.output_format}</td>
                  <td className="px-4 py-3">
                    <div className="w-24">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>{task.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-primary-500 h-1.5 rounded-full transition-all duration-500"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(task.created_at).toLocaleString('zh-CN')}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        to={`/tasks/${task.id}`}
                        className="text-primary-600 hover:text-primary-700 text-xs font-medium"
                      >
                        详情
                      </Link>
                      {task.status === 'completed' && (
                        <>
                          <a
                            href={tasksApi.downloadVideo(task.id)}
                            target="_blank"
                            className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 text-xs font-medium"
                          >
                            <Film className="w-3.5 h-3.5" />
                            视频
                          </a>
                          {task.result_url && (
                            <a
                              href={tasksApi.download(task.id)}
                              target="_blank"
                              className="inline-flex items-center gap-1 text-green-600 hover:text-green-700 text-xs font-medium"
                            >
                              <Download className="w-3.5 h-3.5" />
                              字幕
                            </a>
                          )}
                        </>
                      )}
                      <button
                        onClick={() => handleDelete(task.id)}
                        className="inline-flex items-center gap-1 text-red-500 hover:text-red-700 text-xs font-medium"
                        title="删除任务"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
