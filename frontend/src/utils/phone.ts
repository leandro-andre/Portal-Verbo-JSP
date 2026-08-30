export function onlyDigits(value: string) {
  return value.replace(/\D/g, '')
}

export function normalizeBrazilianMobile(value: string) {
  return onlyDigits(value).slice(0, 11)
}

export function formatBrazilianMobile(value?: string | null) {
  const digits = normalizeBrazilianMobile(value || '')
  if (!digits) {
    return ''
  }
  if (digits.length <= 2) {
    return `(${digits}`
  }
  if (digits.length <= 7) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
  }
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
}

export function isValidBrazilianMobile(value: string) {
  const digits = onlyDigits(value)
  return digits.length === 11 && digits[2] === '9'
}
