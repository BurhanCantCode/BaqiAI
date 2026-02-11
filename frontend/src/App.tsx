import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppProvider } from '@/context/AppContext'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import Invest from '@/pages/Invest'
import Portfolio from '@/pages/Portfolio'
import Analysis from '@/pages/Analysis'
import Insights from '@/pages/Insights'
import Telegram from '@/pages/Telegram'
import Admin from '@/pages/Admin'

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
          <Route path="/telegram" element={<Telegram />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
        </Layout>
      </AppProvider>
    </BrowserRouter>
  )
}
