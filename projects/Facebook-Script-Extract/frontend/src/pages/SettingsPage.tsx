import { Server, Info } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <Server className="w-7 h-7 text-primary-600" />
        设置
      </h1>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
        <div className="flex items-center gap-3">
          <Info className="w-5 h-5 text-primary-600" />
          <div>
            <p className="text-sm font-medium text-gray-900">SSO 统一登录</p>
            <p className="text-xs text-gray-500 mt-0.5">
              当前系统已接入统一身份认证，由 Operation_Manage 管理登录状态
            </p>
          </div>
        </div>
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
        <p className="font-medium mb-1">使用提示</p>
        <ul className="list-disc list-inside space-y-1 text-blue-700">
          <li>本地 Whisper 模式下，首次使用会自动下载模型文件</li>
          <li>模型越大准确度越高，但处理速度越慢</li>
          <li>结果文件默认保留 7 天，过期后自动清理</li>
          <li>如需修改后端配置，请联系管理员编辑 .env 文件</li>
        </ul>
      </div>
    </div>
  )
}
