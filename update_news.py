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
            items.append(dict(title=title,summary=summary,source=source,url=link,category=category,date=date,image=image_of(e)))
    items.sort(key=lambda e:e['date'],reverse=True)
    out=ROOT/'data'/'news-data.js';out.parent.mkdir(exist_ok=True)
    if not items:
        print('Sin datos nuevos: se conserva el archivo anterior')
        return
    out.write_text('window.PLANETA_NEWS = '+json.dumps(items[:110],ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    print('Guardadas',len(items[:110]),'noticias')
if __name__=='__main__':main()
