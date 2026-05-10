import request from './request'

export interface Account {
  id: string
  platform: string
  name: string
  accountId: string | null
  accountType: string | null
  homeUrl: string | null
  market: string | null
  loginEmail: string | null
  loginPhone: string | null
  loginPassword: string | null
  linkedPhone: string | null
  registeredAt: string | null
  commonDevices: string | null
  status: string
  followerCount: number
  persona: string | null
  remark: string | null
  customGroup: string | null
  group: { id: string; name: string } | null
  operators: { id: string; realName: string }[]
  tags: string[]
  createdAt: string
}

export interface AccountGroup {
  id: string
  name: string
  description: string | null
  _count: { accounts: number }
}

export const getAccounts = (params?: {
  platform?: string
  status?: string
  groupId?: string
  search?: string
}): Promise<Account[]> => request.get('/accounts', { params })

export const createAccount = (data: any): Promise<Account> => request.post('/accounts', data)

export const updateAccount = (id: string, data: any): Promise<Account> =>
  request.put(`/accounts/${id}`, data)

export const deleteAccount = (id: string): Promise<void> => request.delete(`/accounts/${id}`)

export const getAccountGroups = (): Promise<AccountGroup[]> => request.get('/accounts/groups/all')

export const createAccountGroup = (data: any): Promise<AccountGroup> =>
  request.post('/accounts/groups', data)

export const updateAccountGroup = (id: string, data: any): Promise<AccountGroup> =>
  request.put(`/accounts/groups/${id}`, data)

export const deleteAccountGroup = (id: string): Promise<void> =>
  request.delete(`/accounts/groups/${id}`)
