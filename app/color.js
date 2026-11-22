.pragma library
// Camenix · conti sui colori per il selettore (nessun accesso a file o rete: solo numeri)

function clamp(x, a, b) { return Math.min(b, Math.max(a, x)) }

// "#RRGGBB" o "RRGGBB" (maiuscole o minuscole) -> "#RRGGBB" maiuscolo; qualsiasi altra cosa -> ""
function normHex(text) {
    if (typeof text !== "string") return ""
    const t = text.trim()
    const m = /^#?([0-9A-Fa-f]{6})$/.exec(t)
    return m ? "#" + m[1].toUpperCase() : ""
}

function hexToRgb(hex) {
    const h = normHex(hex)
    if (!h) return null
    return { r: parseInt(h.substr(1, 2), 16), g: parseInt(h.substr(3, 2), 16), b: parseInt(h.substr(5, 2), 16) }
}

function rgbToHex(r, g, b) {
    const p = v => { const s = Math.round(clamp(Number(v) || 0, 0, 255)).toString(16).toUpperCase(); return s.length < 2 ? "0" + s : s }
    return "#" + p(r) + p(g) + p(b)
}

// r,g,b 0..255 -> h 0..360, s 0..1, v 0..1
function rgbToHsv(r, g, b) {
    r /= 255; g /= 255; b /= 255
    const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min
    let h = 0
    if (d > 0) {
        if (max === r) h = ((g - b) / d) % 6
        else if (max === g) h = (b - r) / d + 2
        else h = (r - g) / d + 4
        h *= 60
        if (h < 0) h += 360
    }
    return { h: h, s: max === 0 ? 0 : d / max, v: max }
}

// h 0..360, s 0..1, v 0..1 -> r,g,b 0..255
function hsvToRgb(h, s, v) {
    h = ((Number(h) || 0) % 360 + 360) % 360; s = clamp(Number(s) || 0, 0, 1); v = clamp(Number(v) || 0, 0, 1)
    const c = v * s, x = c * (1 - Math.abs((h / 60) % 2 - 1)), m = v - c
    let rgb
    if (h < 60) rgb = [c, x, 0]
    else if (h < 120) rgb = [x, c, 0]
    else if (h < 180) rgb = [0, c, x]
    else if (h < 240) rgb = [0, x, c]
    else if (h < 300) rgb = [x, 0, c]
    else rgb = [c, 0, x]
    return { r: Math.round((rgb[0] + m) * 255), g: Math.round((rgb[1] + m) * 255), b: Math.round((rgb[2] + m) * 255) }
}

function hsvToHex(h, s, v) { const c = hsvToRgb(h, s, v); return rgbToHex(c.r, c.g, c.b) }

// colori principali di un'immagine già ridotta: data = RGBA (4 byte per pixel).
// Raggruppa i pixel in "secchielli" (16 livelli per canale), poi sceglie i gruppi più presenti,
// preferendo quelli più vivaci e scartando quelli troppo simili a uno già scelto.
function palette(data, n, minDist) {
    n = n || 8
    minDist = minDist || 56
    const len = data ? data.length : 0
    const buckets = {}
    for (let i = 0; i + 3 < len; i += 4) {
        if (data[i + 3] < 128) continue                          // pixel trasparenti: ignorati
        const r = data[i], g = data[i + 1], b = data[i + 2]
        const k = ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4)
        const e = buckets[k] || (buckets[k] = { r: 0, g: 0, b: 0, n: 0 })
        e.r += r; e.g += g; e.b += b; e.n++
    }
    const list = []
    for (const k in buckets) {
        const e = buckets[k]
        const r = e.r / e.n, g = e.g / e.n, b = e.b / e.n
        const s = rgbToHsv(r, g, b).s
        list.push({ r: r, g: g, b: b, score: e.n * (0.35 + s) })
    }
    list.sort((a, b) => b.score - a.score)
    const out = []
    for (let i = 0; i < list.length && out.length < n; i++) {
        const c = list[i]
        let far = true
        for (let j = 0; j < out.length; j++) {
            const o = out[j]
            if (Math.hypot(c.r - o.r, c.g - o.g, c.b - o.b) < minDist) { far = false; break }
        }
        if (far) out.push({ r: c.r, g: c.g, b: c.b })
    }
    return out.map(c => rgbToHex(c.r, c.g, c.b))
}

function lum(hex) {
    const c = hexToRgb(hex)
    if (!c) return 0
    const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4) }
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b)
}

function contrast(a, b) {
    const la = lum(a), lb = lum(b)
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
}

// palette proposta dai colori di uno sfondo (quelli trovati da palette()).
// L'accento è il colore più vivace, i bordi vanno dal più vivace al secondo; sfondo e testo delle isole
// sono chiari (o scuri) con una punta della stessa tinta, e il testo è sempre leggibile.
function suggest(list, dark) {
    const cols = (list || []).map(normHex).filter(h => h !== "")
    if (!cols.length) return null
    const info = cols.map(h => { const c = hexToRgb(h), v = rgbToHsv(c.r, c.g, c.b); return { hex: h, h: v.h, s: v.s, v: v.v } })
    const vivid = info.slice().sort((a, b) => b.s * b.v - a.s * a.v)
    const a1 = vivid[0]
    const a2 = vivid.find(c => Math.abs(c.h - a1.h) > 25 && c.s > 0.15) || vivid[1] || a1
    const glass = dark ? hsvToHex(a1.h, Math.min(0.35, a1.s), 0.14) : hsvToHex(a1.h, Math.min(0.06, a1.s), 0.985)
    let text = dark ? hsvToHex(a1.h, Math.min(0.08, a1.s), 0.97) : hsvToHex(a1.h, Math.min(0.4, a1.s), 0.15)
    if (contrast(text, glass) < 4.5) text = dark ? "#FFFFFF" : "#1A1A1A"
    return {
        glass: glass, text: text,
        accent: a1.hex, accent2: a2.hex,
        secondary: hsvToHex(a2.h, Math.min(0.45, Math.max(0.2, a2.s)), dark ? 0.7 : 0.88),
        borderFrom: a1.hex, borderTo: a2.hex
    }
}
