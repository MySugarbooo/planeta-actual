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
import re
import sys

ROOT=pathlib.Path(__file__).parent
NEWS=ROOT/"data"/"news-data.js"
CACHE=ROOT/"data"/"translations-cache.json"

def read_news():
    data=NEWS.read_text(encoding="utf-8").strip()
    prefix="window.MEXICO_INFORMA_NEWS = "
    if not data.startswith(prefix):
        raise ValueError("Unexpected news-data.js format")
    return json.loads(data[len(prefix):].rstrip(";").strip())

def write_news(rows):
    NEWS.write_text("window.MEXICO_INFORMA_NEWS = "+json.dumps(rows,ensure_ascii=False,indent=2)+";\n",encoding="utf-8")

def looks_garbage(text, original=""):
    """Detecta traducciones corruptas del traductor automático.

    El modelo a veces devuelve un token repetido hasta el infinito
    (p. ej. "mainstremainstremain...") en vez de una traducción.
    Esos valores nunca deben publicarse ni guardarse en caché:
    sin traducción en inglés, la página muestra el texto en español.
    """
    t=(text or "").strip().lower()
    if not t:
        return False
    if "mainstremain" in t:
        return True
    if re.search(r"(\w{3,})(?:\s*\1){3,}", t):
        return True
    for n in (5, 8, 10, 12):
        sub=t[:n]
        if sub and len(t) >= 4*n and not t.replace(sub, "").strip():
            return True
    if original and len(t) > 3*len(original.strip()) and len(t) > 120:
        return True
    return False

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
    # Limpia traducciones corruptas ya guardadas para retraducirlas.
    for row in rows:
        for field in ("title","summary","resumen"):
            if looks_garbage(row.get(field+"_en"), row.get(field,"")):
                del row[field+"_en"]
    missing=0
    for row in rows:
        for field in ("title","summary","resumen"):
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
    changed=False
    rejected={"empty":0,"identical":0,"garbage":0}
    garbage_samples=[]
    for row in rows:
        for field in ("title","summary","resumen"):
            original=str(row.get(field,"")).strip()
            if not original:continue
            key=hashlib.sha256(original.encode("utf-8")).hexdigest()
            previous=cache.get(key) or row.get(field+"_en")
            if previous and looks_garbage(previous, original):
                previous=None
            if previous:
                if row.get(field+"_en")!=previous:
                    row[field+"_en"]=previous
                    changed=True
                continue
            try:
                english=translate(original).strip()
                # Do not present unchanged Spanish as a completed translation,
                # and never store a garbled machine output.
                if english and english!=original and not looks_garbage(english, original):
                    row[field+"_en"]=english
                    cache[key]=english
                    success+=1
                    changed=True
                elif not english:
                    rejected["empty"]+=1
                elif english==original:
                    rejected["identical"]+=1
                else:
                    rejected["garbage"]+=1
                    if len(garbage_samples)<3:
                        garbage_samples.append(english[:80])
            except Exception as exc:
                print("Translation skipped for an item:",repr(exc))
    # Guardar siempre que alguna traducción (nueva o restaurada de caché)
    # se haya aplicado: antes, con success==0, se perdían incluso las
    # restauradas de caché y el archivo quedaba sin inglés.
    if changed:
        write_news(rows)
    if success:
        CACHE.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("New translations:",success,"| translated stories:",sum(bool(n.get("title_en")) for n in rows),"/",len(rows))
    if sum(rejected.values()):
        print("Rejected translations:",rejected,"| samples:",garbage_samples)

if __name__=="__main__":main()
