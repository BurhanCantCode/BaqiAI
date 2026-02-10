import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 120000,
})

export const baqiApi = {
  // Health
  health: () => api.get('/health'),

  // Demo
  generateSyntheticData: () => api.post('/demo/synthetic-data'),

  // Users
  register: (data: { name: string; phone: string; age?: number; monthly_income?: number }) =>
    api.post('/users/register', data),
  getProfile: (id: number) => api.get(`/users/${id}/profile`),
  submitRiskQuiz: (id: number, answers: number[]) =>
    api.post(`/users/${id}/risk-quiz`, { answers }),

  // Transactions
  getAnalysis: (userId: number) => api.get(`/transactions/${userId}/analysis`),
  getTransactions: (userId: number) => api.get(`/transactions/${userId}/list`),

  // Recommendations (long-running)
  generateRecommendation: (userId: number) =>
    api.post('/recommendations/generate', { user_id: userId }, { timeout: 180000 }),

  // Investments
  executeInvestment: (userId: number, portfolio: any[]) =>
    api.post('/investments/execute', { user_id: userId, portfolio }),

  // Portfolio
  getPortfolio: (userId: number) => api.get(`/portfolio/${userId}`),
  rebalance: (userId: number) => api.post(`/portfolio/${userId}/rebalance`),
}

export default api
