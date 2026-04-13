import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>('dummy-token')
  const user = ref<{ id: string; username: string; role: string } | null>({
    id: 'anonymous',
    username: 'anonymous',
    role: 'admin'
  })

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const login = async () => {
    // 简化版：直接设置 token
    setToken('dummy-token')
    user.value = { id: 'anonymous', username: 'anonymous', role: 'admin' }
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  const isLoggedIn = () => true

  const isAdmin = () => true

  return {
    token,
    user,
    setToken,
    login,
    logout,
    isLoggedIn,
    isAdmin
  }
})
