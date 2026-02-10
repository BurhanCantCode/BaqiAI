import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppProvider } from '@/context/AppContext'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import Invest from '@/pages/Invest'
import Portfolio from '@/pages/Portfolio'
import Analysis from '@/pages/Analysis'
import Insights from '@/pages/Insights'

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/invest" element={<Invest />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/analysis" element={<Analysis />} />
        </Routes>
        </Layout>
      </AppProvider>
    </BrowserRouter>
  )
}
