#!/usr/bin/env python3
"""Actualiza noticias desde feeds RSS públicos y conserva atribución."""
import json, re, html, pathlib, datetime, hashlib, unicodedata
import feedparser
from urllib.parse import urlparse

ROOT=pathlib.Path(__file__).parent
FEEDS=[
 ("El Universal","Nación","https://www.eluniversal.com.mx/arc/outboundfeeds/rss/?outputType=xml"),
 ("La Jornada","Nación","https://www.jornada.com.mx/rss/edicion.xml?v=1"),
 ("El Financiero","Economía","https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml"),
 ("El Economista","Economía","https://www.eleconomista.com.mx/rss/ultimas-noticias"),
 ("Expansión","Economía","https://expansion.mx/rss"),
 ("Infobae México","Nación","https://www.infobae.com/arc/outboundfeeds/rss/category/mexico/"),
 ("Xataka México","Tecnología","https://www.xataka.com.mx/index.xml"),
 ("Diario de Yucatán","Estados","https://www.yucatan.com.mx/feed"),
]
CATEGORY_PATTERNS = [
 ("Seguridad", r"\b(homicidios?|secuestros?|cártel|cartel|narco|balacera|feminicidio|desaparecidos?|guardia nacional|fiscalía|violencia|extorsión)\b"),
 ("Deportes", r"\b(fútbol|futbol|futbolista|liga mx|liguilla|jornada|estadio|goles?|mundial|ol[ií]mpic[oa]s?|f1|fórmula 1|gran premio|boxeo|canelo|checo pérez|béisbol|beisbol|tenis|selección|tricolor|atleta|deportivo|copa del mundo|mundial de clubes|vs)\b"),
 ("Medio Ambiente", r"\b(clima|climátic[oa]|huracán|tormenta|sequía|biodiversidad|especies|contaminación|glaciar|deshielo|incendios forestales|medio ambiente|calentamiento global|energía renovable|vida silvestre|emisiones)\b"),
 ("Tecnología", r"\b(inteligencia artificial|tecnología|tecnológicas|microchip|chip|rob[oó]t|ciberseguridad|redes sociales|algoritmo|software|internet|digital|plataforma|chatgpt)\b"),
 ("Ciencia", r"\b(científic[oa]s?|investigaci[oó]n|experimento|astronom|telescopio|planeta|espacial|nasa|satélite|biología|física cuántica|neurociencia|descubrimiento)\b"),
 ("Salud", r"\b(salud|hospital|vacuna|enfermedad|pandemia|medicamento|médic[oa]s?|tratamiento|cáncer|virus|pacientes|sanitari[oa]|infecci[oó]n)\b"),
 ("Estados", r"\b(jalisco|nuevo león|puebla|guanajuato|veracruz|chiapas|oaxaca|sinaloa|sonora|chihuahua|coahuila|tamaulipas|michoacán|guerrero|hidalgo|morelos|querétaro|san luis potosí|zacatecas|durango|nayarit|colima|tlaxcala|campeche|quintana roo|baja california|tabasco|yucatán|aguascalientes|ciudad de méxico|estado de méxico|cdmx|gobernador[a]?|alcalde|alcaldesa|municipio|ayuntamiento)\b"),
 ("Economía", r"\b(economía|económic[oa]|inflación|finanzas|mercado|bolsa|aranceles|comercio|banco|impuesto|recaudaci[oó]n|empleo|salarios|empresas|precio|petróleo|inversión)\b"),
 ("Política", r"\b(eleccion(?:es)?|electoral|presidencial|presidente|parlamento|congreso|gobierno|diputad[oa]|senador|polític[oa]|votantes|votaci[oó]n|candidato|ministro|trump|midterms|diplomacia|refer[eé]ndum|republican[oa]|demócrata)\b"),
 ("Cultura", r"\b(cultura|cultural|cine|película|música|musical|cantante|artista|festival|libro|literatura|novela|museo|arte|exposición|teatro|actor|actriz|concierto|premios oscar)\b"),
]
def classify(title, summary, fallback):
    content = title + " " + summary
    for name, pattern in CATEGORY_PATTERNS:
        if re.search(pattern, content, re.I):
            return name
    return "Nacional" if fallback == "Mundo" else fallback

# Solo noticias de México. Deportes solo si hay deportistas/equipos mexicanos.
def norm_text(s):
    s=unicodedata.normalize('NFKD',(s or '').lower())
    s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9 ]',' ',s)
MEXICO_SIGNALS=[
 'mexico','mexicana','mexicano','mexicanas','mexicanos','cdmx','ciudad de mexico','estado de mexico','edomex',
 'jalisco','nuevo leon','puebla','guanajuato','veracruz','chiapas','oaxaca','sinaloa','sonora','chihuahua','coahuila','tamaulipas','michoacan','guerrero','hidalgo','morelos','queretaro','san luis potosi','zacatecas','durango','nayarit','colima','tlaxcala','campeche','quintana roo','baja california','tabasco','yucatan','aguascalientes','baja california sur',
 'guadalajara','monterrey','tijuana','merida','acapulco','cancun','mazatlan','toluca','morelia','tulum','cozumel','chapultepec','zocalo','metrobus','hoy no circula','pesos','salario','salarios','conasami',
 'imss','issste','pemex','cfe','banxico','inegi','ine','asf','taddei','auditoria superior','cofepris','sat','sep','sre','sedena','semar','guardia nacional','morena','sheinbaum','lopez obrador','amlo','senado','diputados','suprema corte','scjn','profeco','conagua','inah','inahfest','conade','femexfut','banamex','banorte','cnog','senasica','secretaria de las mujeres',
 'iztacalco','iztapalapa','coyoacan','azcapotzalco','gustavo a madero','xochimilco','tlahuac','benito juarez','miguel hidalgo','alvaro obregon','venustiano carranza','ecatepec','naucalpan','tlanepantla','zapopan','playa del carmen','los cabos','puerto vallarta','san miguel de allende',
]
MEXICAN_SPORTS=[
 'liga mx','liga bbva','bbva','liguilla','chivas','cruz azul','pumas','tigres','rayados','pachuca','toluca','santos laguna','atlas','leon','necaxa','mazatlan','juarez','xolos','queretaro','puebla','san luis','monterrey','club america','aguilas','seleccion mexicana','seleccion nacional','el tri','tricolor','checo perez','canelo','saul alvarez','mexicana','mexicano','mexicanas','mexicanos','juegos olimpicos','atleta mexicano','estadio azteca','estadio bbva','estadio akron',
 'mexico vence','mexico gana','mexico clasifica','mexico empata','mexico debuta','mexico juega','mexico enfrenta','mexico cae','mexico pierde','mexico avanza','mexico logra','mexico consigue','mexico suma','triunfo de mexico','victoria de mexico','derrota de mexico',
]
SPORTS_TITLE_WORDS=[
 'futbol','futbolista','liga','gol','goles','mundial','olimpic','f1','formula 1','gran premio','boxeo','beisbol','nfl','nba','tenis','vs','jornada','estadio','liguilla','copa del mundo','seleccion','tricolor','checo','canelo','pelea','peleador',
]
def _has(text,words):
    return any(re.search(r'\b'+re.escape(w)+r'\b',text) for w in words)
def is_mexico_news(title,summary,category):
    t=norm_text(title); text=norm_text(title+' '+summary)
    if category=='Deportes' or _has(t,SPORTS_TITLE_WORDS):
        return _has(text,MEXICAN_SPORTS)
    return _has(text,MEXICO_SIGNALS)

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
    items=[]; seen=set(); filtered=0
    for source, category, url in FEEDS:
        try:
            feed=feedparser.parse(url,request_headers={'User-Agent':'MexicoInforma/1.0 (RSS reader)'})
            print(source,len(feed.entries), 'http',feed.get('status'))
        except Exception as e:
            print('Feed error',source,e);continue
        for e in feed.entries[:40]:
            title=plain(e.get('title','')); link=e.get('link','')
            if len(title)<15 or not link.startswith('https://'):continue
            key=re.sub(r'[^a-z0-9]','',title.lower())[:90]
            if key in seen:continue
            seen.add(key)
            summary=plain(e.get('summary','') or e.get('description',''))
            summary=summary[:360].rsplit(' ',1)[0]+'…' if len(summary)>360 else summary
            date=e.get('published','') or e.get('updated','')
            try:
                dt=datetime.datetime(*e.published_parsed[:6],tzinfo=datetime.timezone.utc)
                date=dt.astimezone(datetime.timezone(datetime.timedelta(hours=-6))).strftime('%Y-%m-%d %H:%M')
            except Exception:
                date=date[:16]
            image=image_of(e)
            cat=classify(title,summary,category)
            if not is_mexico_news(title,summary,cat):
                filtered+=1; continue
            items.append(dict(title=title,summary=summary,source=source,url=link,category=cat,date=date,image=image_of(e)))
    items.sort(key=lambda x:x['date'],reverse=True)
    try:
        previous=json.loads((ROOT/'data'/'news-data.js').read_text(encoding='utf-8')[14:].rsplit(';\n',1)[0]) if (ROOT/'data'/'news-data.js').exists() else []
    except Exception:
        previous=[]
    known={re.sub(r'[^a-z0-9]','',i.get('title','').lower())[:90] for i in previous}
    items += [i for i in previous if re.sub(r'[^a-z0-9]','',i.get('title','').lower())[:90] not in seen]
    data='const NEWS_DATA = '+json.dumps(items[:110],ensure_ascii=False,indent=1)+';\n'
    h=hashlib.sha256(data.encode()).hexdigest()[:12]
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data'/'news-data.js').write_text(data,encoding='utf-8')
    print('Guardadas',len(items[:110]),'noticias')
    print('Filtradas (no México):',filtered)
if __name__=='__main__':main()
