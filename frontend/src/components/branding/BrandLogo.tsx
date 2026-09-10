type BrandLogoVariant = 'mark' | 'horizontal'
type BrandLogoTone = 'light' | 'dark'

type BrandLogoProps = {
  variant?: BrandLogoVariant
  tone?: BrandLogoTone
  className?: string
  decorative?: boolean
}

const publicBaseUrl = import.meta.env.BASE_URL.endsWith("/")
  ? import.meta.env.BASE_URL
  : `${import.meta.env.BASE_URL}/`

const brandAssets: Record<BrandLogoVariant, string> = {
  mark: `${publicBaseUrl}branding/logo-mark-official.png`,
  horizontal: `${publicBaseUrl}branding/logo-horizontal-official.png`,
}

function BrandLogo({
  variant = 'mark',
  tone = 'dark',
  className = '',
  decorative = false,
}: BrandLogoProps) {
  return (
    <img
      className={`brand-logo brand-logo--${variant} brand-logo--${tone}${className ? ` ${className}` : ''}`}
      src={brandAssets[variant]}
      alt={decorative ? '' : 'Verbo da Vida'}
      aria-hidden={decorative ? true : undefined}
    />
  )
}

export default BrandLogo
