import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/fbse/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface TaskCreateRequest {
  url: string
  language?: string
  output_format?: 'txt' | 'srt' | 'vtt' | 'json'
  use_local?: boolean
  model_size?: 'tiny' | 'base' | 'small' | 'medium' | 'large-v3'
  device?: 'cpu' | 'cuda'
}

export interface TaskInfo {
  id: string
  status: 'pending' | 'downloading' | 'extracting_audio' | 'transcribing' | 'completed' | 'failed'
  url: string
  language: string
  output_format: string
  use_local: boolean
  model_size: string
  created_at: string
  updated_at: string | null
  completed_at: string | null
  error_message: string | null
  result_url: string | null
  progress: number
}

export interface TaskResult {
  id: string
  status: string
  language: string | null
  duration: number | null
  segments: Array<{
    id: number
    start: number
    end: number
    text: string
    speaker?: string
  }> | null
  full_text: string | null
  output_file: string | null
  video_url: string | null
  error_message: string | null
}

export const tasksApi = {
  create: (data: TaskCreateRequest) => api.post<TaskInfo>('/tasks', data),
  list: (skip = 0, limit = 20) => api.get<TaskInfo[]>(`/tasks?skip=${skip}&limit=${limit}`),
  get: (id: string) => api.get<TaskInfo>(`/tasks/${id}`),
  getResult: (id: string) => api.get<TaskResult>(`/tasks/${id}/result`),
  delete: (id: string) => api.delete(`/tasks/${id}`),
  clearAll: () => api.delete('/tasks'),
  download: (id: string) => `${API_BASE}/tasks/${id}/download`,
  downloadVideo: (id: string) => `${API_BASE}/tasks/${id}/download-video`,
}

export const healthApi = {
  check: () => api.get('/health'),
}

export function wsUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/fbse/ws/tasks`
}
