"""Descarga las emergencias de las últimas 24 h de la página pública de los Bomberos del Perú
y las guarda como JSON para el visor Geo-Line Pluz.

Uso: python emergencias.py salida.json
Solo usa la biblioteca estándar de Python. Si la página no responde, escribe el JSON con el campo
"error" y termina sin fallar, para que la publicación del sitio continúe."""
import datetime, html, json, re, sys, urllib.request

URL = 'https://sgonorte.bomberosperu.gob.pe/24horas'
LIMA = datetime.timezone(datetime.timedelta(hours=-5))

def texto(fragmento):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragmento))).strip()

def fecha_iso(t):
    t = t.replace('a.m.', 'AM').replace('p.m.', 'PM').replace('a. m.', 'AM').replace('p. m.', 'PM')
    try:
        return datetime.datetime.strptime(t, '%d/%m/%Y %I:%M:%S %p').replace(tzinfo=LIMA).isoformat()
    except ValueError:
        return None

def leer():
    req = urllib.request.Request(URL, headers={'User-Agent': 'GeoLinePluz/1.0 (consulta cada 10 min)'})
    pagina = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')
    items = []
    for fila in re.findall(r'<tr[^>]*>(.*?)</tr>', pagina, re.S):
        celdas = re.findall(r'<td[^>]*>(.*?)</td>', fila, re.S)
        if len(celdas) < 6:
            continue
        parte, fecha, lugar, tipo, estado = (texto(c) for c in celdas[:5])
        unidades = [texto(u) for u in re.findall(r'<li[^>]*>(.*?)</li>', celdas[5], re.S)]
        lat = lon = None
        m = re.search(r'\((-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\)', lugar)
        if m:
            la, lo = float(m.group(1)), float(m.group(2))
            if la or lo:
                lat, lon = la, lo
            lugar = lugar[:m.start()] + lugar[m.end():]
        lugar = re.sub(r'\s+', ' ', lugar).strip()
        direccion, _, distrito = lugar.rpartition(' - ') if ' - ' in lugar else (lugar, '', '')
        direccion = re.sub(r'\s*Nro\.\s*0*\s*$', '', direccion.strip())
        items.append({'parte': parte, 'fecha': fecha_iso(fecha), 'fecha_txt': fecha, 'direccion': direccion,
                      'distrito': distrito.strip(), 'tipo': tipo, 'estado': estado, 'unidades': unidades,
                      'lat': lat, 'lon': lon})
    return items

def main(salida):
    res = {'fuente': URL, 'consultado': datetime.datetime.now(LIMA).isoformat(timespec='seconds'), 'items': [], 'error': None}
    try:
        res['items'] = leer()
    except Exception as e:  # la publicación del sitio no debe detenerse por esto
        res['error'] = f'{type(e).__name__}: {e}'
    with open(salida, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False)
    print(len(res['items']), 'emergencias', '| error:', res['error'])

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'emergencias.json')
