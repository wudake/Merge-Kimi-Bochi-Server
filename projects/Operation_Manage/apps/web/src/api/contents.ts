import request from './request'

export interface ContentItem {
  id: string
  title: string
  status: string
  plannedPublishAt: string | null
  actualPublishAt: string | null
  publishUrl: string | null
  contentType: string | null
  script: string | null
  description: string | null
  topic: { id: string; title: string } | null
  operator: { id: string; realName: string } | null
  accounts: { id: string; name: string; platform: string }[]
  createdAt: string
}

export const getContents = (params?: {
  status?: string
  operatorId?: string
  accountId?: string
  search?: string
  startDate?: string
  endDate?: string
}): Promise<ContentItem[]> => request.get('/contents', { params })

export const getCalendarContents = (params: {
  startDate: string
  endDate: string
  operatorId?: string
  accountId?: string
}): Promise<ContentItem[]> => request.get('/contents/calendar', { params })

export const createContent = (data: any): Promise<ContentItem> => request.post('/contents', data)

export const updateContent = (id: string, data: any): Promise<ContentItem> =>
  request.put(`/contents/${id}`, data)

export const updateContentStatus = (id: string, status: string): Promise<ContentItem> =>
  request.put(`/contents/${id}/status`, { status })

export const deleteContent = (id: string): Promise<void> => request.delete(`/contents/${id}`)
