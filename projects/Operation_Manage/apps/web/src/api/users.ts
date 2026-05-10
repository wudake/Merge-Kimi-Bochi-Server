import request from './request'

export interface User {
  id: string
  username: string
  realName: string
  role: string
  email: string | null
  phone: string | null
  status: string
  createdAt: string
}

export const getUsers = (): Promise<User[]> => request.get('/users')

export const createUser = (data: any): Promise<User> => request.post('/users', data)

export const updateUser = (id: string, data: any): Promise<User> =>
  request.put(`/users/${id}`, data)

export const deleteUser = (id: string): Promise<void> => request.delete(`/users/${id}`)
