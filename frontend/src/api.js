async function handle(r) {
  if (!r.ok) {
    let msg = await r.text()
    try {
      const j = JSON.parse(msg)
      if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch { /* keep raw text */ }
    throw new Error(msg)
  }
  return r.json()
}
const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
export async function getJSON(path) { return handle(await fetch(path)) }
export async function postJSON(path, body) { return handle(await fetch(path, opts('POST', body))) }
export async function putJSON(path, body) { return handle(await fetch(path, opts('PUT', body))) }
