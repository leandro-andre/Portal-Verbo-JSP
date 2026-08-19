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

export async function ensureCsrfCookie() {
  if (!getCsrfToken()) {
    csrfPromise ??= fetch('/api/auth/csrf/', {
      credentials: 'same-origin',
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
}

export async function csrfJsonHeaders() {
  await ensureCsrfCookie()
  return {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken(),
  }
}
