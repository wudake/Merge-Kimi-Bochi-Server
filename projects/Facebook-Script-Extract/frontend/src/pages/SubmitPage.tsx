import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Link2, Loader2, Mic, Cpu, Globe, FileText, CheckCircle2 } from 'lucide-react'
import { tasksApi } from '../api/client'
import { isValidVideoUrl } from '../utils/validation'

export default function SubmitPage() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [language, setLanguage] = useState('en')
  const [format, setFormat] = useState<'json' | 'txt' | 'srt' | 'vtt'>('json')
  const [useLocal, setUseLocal] = useState(true)
  const [modelSize, setModelSize] = useState<'tiny' | 'base' | 'small' | 'medium' | 'large-v3'>('tiny')
  const [device, setDevice] = useState<'cpu' | 'cuda'>('cpu')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const isSubmittingRef = useRef(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isSubmittingRef.current) return
    isSubmittingRef.current = true
    setError('')
    setSuccess('')
    setLoading(true)

    if (!isValidVideoUrl(url)) {
      setError('无效的链接，仅支持 Facebook 视频、YouTube 视频和 Facebook Ads Library 链接')
      setLoading(false)
      isSubmittingRef.current = false
      return
    }

    try {
      const res = await tasksApi.create({
        url,
        language,
        output_format: format,
        use_local: useLocal,
        model_size: modelSize,
        device,
      })
      setSuccess(`任务已创建: ${res.data.id}`)
      setTimeout(() => navigate(`/tasks/${res.data.id}`), 800)
    } catch (err: any) {
      setError(err.response?.data?.detail || '提交失败，请检查链接和后端服务')
    } finally {
      setLoading(false)
      isSubmittingRef.current = false
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
        <Mic className="w-7 h-7 text-primary-600" />
        新建转写任务
      </h1>

      <p className="text-sm text-gray-500 mb-6 leading-relaxed">
        粘贴 Facebook、YouTube 或 Facebook Ads Library 视频链接，系统自动下载视频、提取音频并完成语音识别，输出 TXT / SRT / VTT / JSON 格式的文字脚本。支持本地 Whisper 模型（免费）或 OpenAI API（付费）两种转写引擎。
      </p>

      <form onSubmit={handleSubmit} className="space-y-5 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        {/* URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            视频链接（Facebook / YouTube / Ads Library）
          </label>
          <div className="relative">
            <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="url"
              required
              placeholder="Facebook 视频、YouTube 视频，或 facebook.com/ads/library/?id=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            />
          </div>
        </div>

        {/* 语言 + 格式 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5 flex items-center gap-1">
              <Globe className="w-3.5 h-3.5" /> 语言
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="auto">自动检测</option>
              <option value="zh">中文</option>
              <option value="en">English</option>
              <option value="ja">日本語</option>
              <option value="ko">한국어</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5 flex items-center gap-1">
              <FileText className="w-3.5 h-3.5" /> 输出格式
            </label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value as any)}
              className="w-full px-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="json">JSON（结构化）</option>
              <option value="txt">TXT（纯文本）</option>
              <option value="srt">SRT（字幕）</option>
              <option value="vtt">VTT（字幕）</option>
            </select>
          </div>
        </div>

        {/* 引擎选择 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">转写引擎</label>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setUseLocal(true)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border text-sm font-medium transition-colors ${
                useLocal
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Cpu className="w-4 h-4" />
              本地 Whisper（免费）
            </button>
            <button
              type="button"
              onClick={() => setUseLocal(false)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border text-sm font-medium transition-colors ${
                !useLocal
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Globe className="w-4 h-4" />
              OpenAI API（付费）
            </button>
          </div>
        </div>

        {/* 本地模型选项 */}
        {useLocal && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">模型大小</label>
              <select
                value={modelSize}
                onChange={(e) => setModelSize(e.target.value as any)}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 text-sm"
              >
                <option value="tiny">tiny（最快，准确度低）</option>
                <option value="base">base（快）</option>
                <option value="small">small（平衡）</option>
                <option value="medium">medium（准）</option>
                <option value="large-v3">large-v3（最准，最慢）</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">推理设备</label>
              <select
                value={device}
                onChange={(e) => setDevice(e.target.value as any)}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 text-sm"
              >
                <option value="cpu">CPU（通用）</option>
                <option value="cuda">CUDA（需 NVIDIA 显卡）</option>
              </select>
            </div>
          </div>
        )}

        {/* 提交 */}
        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-60"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mic className="w-4 h-4" />}
          {loading ? '提交中...' : '开始转写'}
        </button>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-50 text-green-700 text-sm rounded-lg px-4 py-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            {success}
          </div>
        )}
      </form>
    </div>
  )
}
