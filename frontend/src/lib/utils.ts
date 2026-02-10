import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const formatPKR = (amount: number) =>
  `PKR ${amount.toLocaleString('en-PK', { maximumFractionDigits: 0 })}`

export const formatUSD = (amount: number) =>
  `$${amount.toLocaleString('en-US', { maximumFractionDigits: 0 })}`

export const formatMoney = (amount: number, currency?: string) =>
  currency === 'PKR' ? formatPKR(amount) : formatUSD(amount)

export const formatPercent = (value: number) =>
  `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
