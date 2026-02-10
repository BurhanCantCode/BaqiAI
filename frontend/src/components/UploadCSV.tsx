import { useState, useRef } from 'react'
import { Upload, FileSpreadsheet, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { uploadApi } from '@/api/upload'

interface UploadCSVProps {
  userId?: number
  onUploadComplete: (data: any) => void
  onCancel: () => void
}

export default function UploadCSV({ userId, onUploadComplete, onCancel }: UploadCSVProps) {
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFileSelect(e.target.files[0])
    }
  }

  const handleFileSelect = async (selectedFile: File) => {
    setError(null)
    setPreview(null)

    // Validate file type
    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      setError('Please upload a CSV file')
      return
    }

    // Validate file size (5MB)
    if (selectedFile.size > 5 * 1024 * 1024) {
      setError('File size must be less than 5MB')
      return
    }

    setFile(selectedFile)

    // Get preview
    try {
      const response = await uploadApi.previewCSV(selectedFile)
      setPreview(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to preview CSV file')
      setFile(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)

    try {
      const response = await uploadApi.uploadCSV(file, userId)
      onUploadComplete(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload CSV file')
    } finally {
      setUploading(false)
    }
  }

  const handleRemoveFile = () => {
    setFile(null)
    setPreview(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-4">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-bold">Upload Bank Statement</h2>
        <p className="text-muted-foreground mt-1">
          Upload your bank statement CSV to analyze your transactions
        </p>
      </div>

      {/* Upload Area */}
      {!file && (
        <Card
          className={`p-8 border-2 border-dashed transition-all cursor-pointer ${
            dragActive
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <Upload className="w-8 h-8 text-primary" />
            </div>
            <div>
              <p className="text-lg font-semibold mb-1">
                Drag and drop your CSV file here
              </p>
              <p className="text-sm text-muted-foreground">
                or click to browse files
              </p>
            </div>
            <Badge variant="secondary" className="text-xs">
              Maximum file size: 5MB
            </Badge>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileInput}
            className="hidden"
          />
        </Card>
      )}

      {/* File Preview */}
      {file && preview && (
        <Card className="p-6 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-green-50 flex items-center justify-center">
                <FileSpreadsheet className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="font-semibold">{file.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(file.size / 1024).toFixed(1)} KB · {preview.total_rows} rows
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemoveFile}
              disabled={uploading}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Detected Columns */}
          <div className="space-y-2">
            <p className="text-sm font-medium">Detected Columns:</p>
            <div className="flex flex-wrap gap-2">
              {preview.detected_columns?.date && (
                <Badge variant="secondary" className="bg-blue-50 text-blue-600 border-blue-200">
                  Date: {preview.detected_columns.date}
                </Badge>
              )}
              {preview.detected_columns?.amount && (
                <Badge variant="secondary" className="bg-green-50 text-green-600 border-green-200">
                  Amount: {preview.detected_columns.amount}
                </Badge>
              )}
              {preview.detected_columns?.description && (
                <Badge variant="secondary" className="bg-purple-50 text-purple-600 border-purple-200">
                  Description: {preview.detected_columns.description}
                </Badge>
              )}
            </div>
          </div>

          {/* Preview Table */}
          <div>
            <p className="text-sm font-medium mb-2">Preview (first 5 rows):</p>
            <div className="border rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr>
                      {preview.headers?.map((header: string, i: number) => (
                        <th key={i} className="px-4 py-2 text-left font-medium">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.preview_rows?.slice(0, 5).map((row: string[], i: number) => (
                      <tr key={i} className="border-t">
                        {row.map((cell: string, j: number) => (
                          <td key={j} className="px-4 py-2 text-muted-foreground">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Error Message */}
      {error && (
        <Card className="p-4 bg-red-50 border-red-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-900">Upload Error</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="flex-1"
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4 mr-2" />
              Upload & Analyze
            </>
          )}
        </Button>
        <Button variant="outline" onClick={onCancel} disabled={uploading}>
          Cancel
        </Button>
      </div>
    </div>
  )
}
