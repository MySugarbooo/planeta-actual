#!/usr/bin/env python3
"""Actualiza noticias desde feeds RSS públicos y conserva atribución."""
import json, re, html, pathlib, datetime, hashlib
import feedparser
from urllib.parse import urlparse

ROOT=pathlib.Path(__file__).parent
FEEDS=[
 ("BBC Mundo","Mundo","https://feeds.bbci.co.uk/mundo/rss.xml"),
 ("DW Español","Mundo","https://rss.dw.com/rdf/rss-sp-all"),
 ("France 24","Mundo","https://www.france24.com/es/rss"),
 ("El País","Mundo","https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"),
 ("El País Economía","Economía","https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada"),
 ("El País Tecnología","Tecnología","https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/tecnologia/portada"),
 ("El País Ciencia","Ciencia","https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/ciencia/portada"),
]
CATEGORY_PATTERNS = [
 ("Deportes", r"\b(fútbol|futbol|liga|tenis|alcaraz|mbappé|madrid|racing|barça|bayern|champions|mundial de clubes|partido|gol|regata|atleta|deportivo|copa del mundo|nba|f1|fórmula 1|gran premio)\b"),
 ("Medio Ambiente", r"\b(clima|climátic[oa]|huracán|tormenta|sequía|biodiversidad|especies|contaminación|glaciar|deshielo|incendios forestales|medio ambiente|calentamiento global|energía renovable|vida silvestre|emisiones)\b"),
 ("Tecnología", r"\b(inteligencia artificial|tecnología|tecnológicas|microchip|chip|rob[oó]t|ciberseguridad|redes sociales|algoritmo|software|internet|digital|plataforma|chatgpt)\b"),
 ("Ciencia", r"\b(científic[oa]s?|investigaci[oó]n|experimento|astronom|telescopio|planeta|espacial|nasa|satélite|biología|física cuántica|neurociencia|descubrimiento)\b"),
 ("Salud", r"\b(salud|hospital|vacuna|enfermedad|pandemia|medicamento|médic[oa]s?|tratamiento|cáncer|virus|pacientes|sanitari[oa]|infecci[oó]n)\b"),
 ("Economía", r"\b(economía|económic[oa]|inflación|finanzas|mercado|bolsa|aranceles|comercio|banco|impuesto|recaudaci[oó]n|empleo|salarios|empresas|precio|petróleo|inversión)\b"),
 ("Política", r"\b(eleccion(?:es)?|electoral|presidencial|presidente|parlamento|congreso|gobierno|diputad[oa]|senador|polític[oa]|votantes|votaci[oó]n|candidato|ministro|trump|midterms|diplomacia|refer[eé]ndum|republican[oa]|demócrata)\b"),
 ("Cultura", r"\b(cultura|cultural|cine|película|música|musical|cantante|artista|festival|libro|literatura|novela|museo|arte|exposición|teatro|actor|actriz|concierto|premios oscar)\b"),
]
def classify(title, summary, fallback):
    content = title + " " + summary
    for name, pattern in CATEGORY_PATTERNS:
        if re.search(pattern, content, re.I):
            return name
    return "Internacional" if fallback == "Mundo" else fallback

def plain(s):
    s=re.sub(r'<[^>]+>',' ',s or '')
    return re.sub(r'\s+',' ',html.unescape(s)).strip()
def image_of(entry):
    for item in entry.get('media_content',[])+entry.get('media_thumbnail',[]):
        u=item.get('url','')
        if u.startswith('https://') and re.search(r'\.(?:jpg|jpeg|png|webp)(?:[?]|$)',u,re.I):
            return u
    for link in entry.get('links',[]):
        if link.get('type','').startswith('image/') and link.get('href','').startswith('https://'):
            return link.get('href')
    return ""
def main():
    items=[]; seen=set()
    for source, category, url in FEEDS:
        try:
            feed=feedparser.parse(url,request_headers={'User-Agent':'PlanetaActual/1.0 (RSS reader)'})
            print(source,len(feed.entries), 'http',feed.get('status'))
        except Exception as e:
            print('Feed error',source,e);continue
        for e in feed.entries[:30]:
            title=plain(e.get('title','')); link=e.get('link','')
            if len(title)<15 or not link.startswith('https://'):continue
            key=re.sub(r'[^a-z0-9]','',title.lower())[:90]
            if key in seen:continue
            seen.add(key)
            summary=plain(e.get('summary','') or e.get('description',''))
            summary=summary[:360].rsplit(' ',1)[0]+'…' if len(summary)>360 else summary
            if not summary:summary='Consulta los detalles en la fuente original.'
            when=e.get('published_parsed') or e.get('updated_parsed')
            date=datetime.datetime(*when[:6],tzinfo=datetime.timezone.utc).isoformat() if when else datetime.datetime.now(datetime.timezone.utc).isoformat()
            items.append(dict(title=title,summary=summary,source=source,url=link,category=classify(title,summary,category),date=date,image=image_of(e)))
    items.sort(key=lambda e:e['date'],reverse=True)
    out=ROOT/'data'/'news-data.js';out.parent.mkdir(exist_ok=True)
    if not items:
        print('Sin datos nuevos: se conserva el archivo anterior')
        return
    out.write_text('window.PLANETA_NEWS = '+json.dumps(items[:110],ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    print('Guardadas',len(items[:110]),'noticias')
if __name__=='__main__':main()
