function PortalHeader() {
  return (
    <header className="portal-header">
      <div className="portal-header__content">
        <div>
          <p className="portal-header__eyebrow">Portal Verbo da Vida</p>
          <strong className="portal-header__title">Jardim São Paulo</strong>
        </div>

        <nav className="portal-nav" aria-label="Navegação principal">
          <a className="portal-nav__link portal-nav__link--active" href="#pessoas">
            Pessoas
          </a>
          <a className="portal-nav__link" href="#departamentos">
            Departamentos
          </a>
          <a className="portal-nav__link" href="#escalas">
            Escalas
          </a>
        </nav>
      </div>
    </header>
  )
}

export default PortalHeader
