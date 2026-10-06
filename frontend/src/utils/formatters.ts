export function formatNumber(value: number): string {
  return value.toLocaleString();
}

export function formatCurrency(value: number, currency: string = 'INR'): string {
  if (currency === 'INR') {
    if (value >= 10000000) {
      return `₹${(value / 10000000).toFixed(1)}Cr`;
    }
    if (value >= 100000) {
      return `₹${(value / 100000).toFixed(1)}L`;
    }
    if (value >= 1000) {
      return `₹${(value / 1000).toFixed(1)}K`;
    }
    return `₹${value.toLocaleString('en-IN')}`;
  }

  // Fallback for USD or others
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toLocaleString()}`;
}

export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatDynamic(value: any, role?: string): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') {
    if (role === 'Currency') return formatCurrency(value);
    if (role === 'Percentage') return formatPercentage(value);
    return formatNumber(value);
  }
  return String(value);
}
