import request from './request'

export interface Topic {
  id: string
  title: string
  contentForm: string
  tags: string[]
  productType: string | null
  contentType: string | null
  source: string | null
  status: string
  usageCount: number
  isCompleted: boolean
  completedAt: string | null
  operatorId: string | null
  publishedAccounts: string | null
  script: string | null
  copywriting: string | null
  remark: string | null
  createdBy: string
  creator: { id: string; realName: string }
  _count: { contents: number }
  createdAt: string
}

export const getTopics = (params?: {
  status?: string
  contentType?: string
  search?: string
  sortBy?: string
}): Promise<Topic[]> => request.get('/topics', { params })

export const createTopic = (data: any): Promise<Topic> => request.post('/topics', data)

export const updateTopic = (id: string, data: any): Promise<Topic> =>
  request.put(`/topics/${id}`, data)

export const deleteTopic = (id: string): Promise<void> => request.delete(`/topics/${id}`)
