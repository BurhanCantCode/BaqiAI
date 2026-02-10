export interface User {
  id: number
  name: string
  phone: string
  age?: number
  risk_profile: string
  halal_preference: boolean
  monthly_income: number
}

export interface SpendingAnalysis {
  total_income: number
  total_spending: number
  fixed: CategoryBreakdown
  discretionary: CategoryBreakdown
  watery: CategoryBreakdown
  baqi_amount: number
  savings_rate: number
  watery_savings_potential: number
  recommended_investment: number
  monthly_breakdown: MonthlyBreakdown[]
}

export interface CategoryBreakdown {
  total: number
  percentage: number
  items: MerchantItem[]
}

export interface MerchantItem {
  merchant: string
  total: number
  count: number
}

export interface MonthlyBreakdown {
  month: string
  income: number
  spending: number
  baqi: number
}

export interface RiskQuizResponse {
  risk_profile: string
  risk_score: number
  allocation: {
    equity: number
    fixed_income: number
    mutual_fund: number
  }
}

export interface PortfolioAllocation {
  asset_name: string
  ticker: string
  asset_type: string
  amount_pkr: number
  percentage: number
  expected_return: number
  is_halal: boolean
  rationale: string
}

export interface RecommendationResult {
  user_id: number
  spending_analysis: {
    total_income: number
    total_spending: number
    baqi_amount: number
    monthly_baqi: number
  }
  risk_profile: string
  recommendation: {
    portfolio?: PortfolioAllocation[]
    total_invested?: number
    expected_annual_return?: number
    summary?: string
    raw_output?: string
  }
}

export interface PortfolioData {
  user_id: number
  holdings: Holding[]
  total_invested: number
  current_value: number
  total_return: number
  return_percentage: number
  snapshots: PortfolioSnapshot[]
}

export interface Holding {
  id: number
  asset_name: string
  ticker: string
  asset_type: string
  amount: number
  quantity: number
  purchase_price: number
  current_price: number
  current_value?: number
  return_pct?: number
  status: string
}

export interface PortfolioSnapshot {
  id: number
  snapshot_date: string
  total_invested: number
  current_value: number
  return_percentage: number
}

// Data Exhaust Insights types
export interface InsightItem {
  title: string
  description: string
  action: string
  category: 'behavioral' | 'saving_opportunity' | 'anomaly' | 'trend' | 'optimization'
  severity: 'info' | 'warning' | 'opportunity'
  impact_pkr: number | null
}

export interface InsightsResponse {
  user_id: number
  insights: InsightItem[]
  data_exhaust: Record<string, any>
  generated_at: string
}

// Agent pipeline types
export interface AgentStep {
  id: string
  name: string
  role: string
  icon: string
  color: string
  status: 'waiting' | 'active' | 'streaming' | 'done'
  output: string
  streamedText: string
}
