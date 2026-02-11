import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 120000,
})

export type DataSource = 'csv' | 'supabase'

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
  getAnalysis: (userId: number, source?: DataSource) =>
    api.get(`/transactions/${userId}/analysis`, { params: source ? { source } : {} }),
  getTransactions: (userId: number, source?: DataSource) =>
    api.get(`/transactions/${userId}/list`, { params: source ? { source } : {} }),

  // Recommendations (long-running)
  generateRecommendation: (userId: number, source?: DataSource) =>
    api.post('/recommendations/generate', { user_id: userId, source }, { timeout: 180000 }),

  // Investments
  executeInvestment: (userId: number, portfolio: any[]) =>
    api.post('/investments/execute', { user_id: userId, portfolio }),

  // Portfolio
  getPortfolio: (userId: number) => api.get(`/portfolio/${userId}`),
  rebalance: (userId: number) => api.post(`/portfolio/${userId}/rebalance`),

  // AI Insights
  getInsights: (userId: number, source?: DataSource) =>
    api.get(`/insights/${userId}`, { params: source ? { source } : {}, timeout: 120000 }),

  // Admin
  getAdminUsers: () => api.get('/admin/users'),
  simulateTransaction: (data: { user_id: number; merchant: string; amount: number }) =>
    api.post('/admin/simulate-transaction', null, { params: data }),
  sendWeeklyReport: (userId: number) =>
    api.post('/admin/send-weekly-report', null, { params: { user_id: userId } }),
  sendNotification: (data: { user_id: number; message: string }) =>
    api.post('/admin/send-notification', null, { params: data }),
}

export default api
