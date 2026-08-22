let csrfPromise: Promise<void> | null = null

function getCookie(name: string) {
  const cookies = document.cookie ? document.cookie.split('; ') : []
  const prefix = `${name}=`
  const cookie = cookies.find((item) => item.startsWith(prefix))
  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : ''
}

export function getCsrfToken() {
  return getCookie('csrftoken')
}

export async function ensureCsrfCookie({ refresh = false }: { refresh?: boolean } = {}) {
  if (!refresh && getCsrfToken()) {
    return
  }

  csrfPromise ??= fetch('/api/auth/csrf/', {
    credentials: 'include',
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error('Nao foi possivel preparar a sessao.')
      }
    })
    .finally(() => {
      csrfPromise = null
    })

  await csrfPromise
}

export async function csrfJsonHeaders({ refresh = false }: { refresh?: boolean } = {}) {
  await ensureCsrfCookie({ refresh })
  return {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken(),
  }
}
