#!/usr/bin/env python3
"""Traducción local y gratuita es→en de titulares y resúmenes RSS.

Solo se publica un campo *_en cuando la traducción terminó correctamente.
Se guardan resultados por texto para evitar volver a traducir cada hora.
"""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import sys

ROOT=pathlib.Path(__file__).parent
NEWS=ROOT/"data"/"news-data.js"
CACHE=ROOT/"data"/"translations-cache.json"

def read_news():
    data=NEWS.read_text(encoding="utf-8").strip()
    prefix="window.PLANETA_NEWS = "
    if not data.startswith(prefix):
        raise ValueError("Unexpected news-data.js format")
    return json.loads(data[len(prefix):].rstrip(";").strip())

def write_news(rows):
    NEWS.write_text("window.PLANETA_NEWS = "+json.dumps(rows,ensure_ascii=False,indent=2)+";\n",encoding="utf-8")

def build_translator():
    import argostranslate.package as package
    import argostranslate.translate as translate
    model_dir=os.environ.get("ARGOS_PACKAGE_DIR")
    if model_dir:
        pathlib.Path(model_dir).mkdir(parents=True,exist_ok=True)
    def installed():
        src=next((x for x in translate.get_installed_languages() if x.code=="es"),None)
        dst=next((x for x in translate.get_installed_languages() if x.code=="en"),None)
        return src.get_translation(dst) if src and dst else None
    ready=installed()
    if ready:return ready.translate
    package.update_package_index()
    match=next((p for p in package.get_available_packages() if p.from_code=="es" and p.to_code=="en"),None)
    if match is None:
        raise RuntimeError("Spanish-English language model missing from Argos package index")
    package.install_from_path(match.download())
    translate.get_installed_languages.cache_clear()
    ready=installed()
    if not ready:raise RuntimeError("Spanish-English translator not installed")
    return ready.translate

def main():
    rows=read_news()
    cache=json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    if not isinstance(cache,dict):cache={}
    missing=0
    for row in rows:
        for field in ("title","summary"):
            original=str(row.get(field,"")).strip()
            if original and not row.get(field+"_en"):
                missing+=1
    print("Missing translations:",missing)
    if not missing:return
    try:
        translate=build_translator()
    except Exception as exc:
        print("Translator unavailable: retaining Spanish text and previous English translations:",repr(exc))
        return
    success=0
    for row in rows:
        for field in ("title","summary"):
            original=str(row.get(field,"")).strip()
            if not original:continue
            key=hashlib.sha256(original.encode("utf-8")).hexdigest()
            previous=cache.get(key) or row.get(field+"_en")
            if previous:
                row[field+"_en"]=previous
                continue
            try:
                english=translate(original).strip()
                # Do not present unchanged Spanish as a completed translation.
                if english and english!=original:
                    row[field+"_en"]=english
                    cache[key]=english
                    success+=1
            except Exception as exc:
                print("Translation skipped for an item:",repr(exc))
    if success:
        write_news(rows)
        CACHE.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("New translations:",success,"| translated stories:",sum(bool(n.get("title_en")) for n in rows),"/",len(rows))

if __name__=="__main__":main()
