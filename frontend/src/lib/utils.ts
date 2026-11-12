import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatTonnes(tonnes: number): string {
  return `${tonnes.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} t`;
}

export function formatCO2(kg: number): string {
  if (kg >= 1000) {
    return `${(kg / 1000).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} t CO₂e`;
  }
  return `${kg.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} kg CO₂e`;
}

