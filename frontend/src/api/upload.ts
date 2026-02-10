import api from '@/api/client'

export const uploadApi = {
  // Upload CSV file
  uploadCSV: (file: File, userId?: number, columnMapping?: {
    dateCol?: string
    amountCol?: string
    descriptionCol?: string
  }) => {
    const formData = new FormData()
    formData.append('file', file)
    if (userId) formData.append('user_id', userId.toString())
    if (columnMapping?.dateCol) formData.append('date_col', columnMapping.dateCol)
    if (columnMapping?.amountCol) formData.append('amount_col', columnMapping.amountCol)
    if (columnMapping?.descriptionCol) formData.append('description_col', columnMapping.descriptionCol)

    return api.post('/upload/csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // Preview CSV before upload
  previewCSV: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    return api.post('/upload/csv/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // Get uploaded CSV info
  getUploadedCSVInfo: (userId: number) =>
    api.get(`/upload/csv/${userId}/info`)
}
