(function(){
const dictionary = {
  es: {
    tagline:"Noticias del mundo",horoscopes:"Horóscopos",latest:"Última hora",loading:"Cargando titulares...",
    selection:"Selección del mundo",related:"También en el mundo",more:"Ver más →",all:"Todas las noticias",
    search:"Buscar noticias, países o temas…",sourceinfo:"Noticias con enlace a la fuente original",
    footer:"© Planeta Actual · Información internacional basada en medios enlazados. Las imágenes proceden de los enlaces de origen cuando están disponibles. Las imágenes no verificadas se señalan como representativas. Los resúmenes automatizados requieren revisión editorial.",
    source:"Fuente",no_news:"Sin noticias para este filtro.",no_more:"No hay más noticias disponibles por ahora.",
    all_shown:"Ya se muestran todas las noticias de esta categoría arriba.",consult:"Consulta la noticia en la fuente original.",
    images:"Imagen proporcionada por el medio de origen",illustration:"Imagen representativa",news:"noticias",
    original:"Este artículo conserva el texto original en español mientras se completa su traducción.",
    category_inicio:"Inicio",category_deportes:"Deportes",category_internacional:"Internacional",category_política:"Política",
    category_economía:"Economía",category_tecnología:"Tecnología",category_ciencia:"Ciencia",
    category_medio_ambiente:"Medio Ambiente",category_cultura:"Cultura",category_salud:"Salud",
    date:"Fecha", english:"English",spanish:"Español"
  },
  en: {
    tagline:"World news",horoscopes:"Horoscopes",latest:"Breaking news",loading:"Loading headlines...",
    selection:"Around the world",related:"Elsewhere in the world",more:"See more →",all:"All stories",
    search:"Search news, countries or topics…",sourceinfo:"Stories link to their original sources",
    footer:"© Planeta Actual · International coverage based on linked news outlets. Photographs come from source publishers when available. Unverified images are labeled as illustrative. Automated summaries require editorial review.",
    source:"Source",no_news:"No stories found for this category.",no_more:"No additional stories available at this time.",
    all_shown:"All stories in this category are already shown above.",consult:"Read the full story at the original source.",
    images:"Image supplied by the original publisher",illustration:"Illustrative image",news:"stories",
    original:"Original Spanish text is shown while the automatic translation is being prepared.",
    category_inicio:"Home",category_deportes:"Sports",category_internacional:"World",category_política:"Politics",
    category_economía:"Economy",category_tecnología:"Technology",category_ciencia:"Science",
    category_medio_ambiente:"Environment",category_cultura:"Culture",category_salud:"Health",
    date:"Date",english:"English",spanish:"Español"
  }
};
let value;
try {
 const urlLang = new URLSearchParams(location.search).get("lang");
 value = urlLang==="en"?"en":urlLang==="es"?"es":localStorage.getItem("pa-lang")==="en"?"en":"es";
} catch(e) {value="es"}
function change(next){
 value=next==="en"?"en":"es";
 try {localStorage.setItem("pa-lang",value)}catch(e){}
 try {
   const u=new URL(location.href);
   if(value==="en")u.searchParams.set("lang","en");else u.searchParams.delete("lang");
   history.replaceState(null,"",u.pathname+u.search+u.hash);
 }catch(e){}
 apply();
}
function get(k){return dictionary[value][k] || dictionary.es[k] || k}
function label(cat){
 return get("category_"+String(cat||"Internacional").toLowerCase().replace(/\s+/g,"_"))
}
function newsText(n,key){
 if(value==="en" && n[key+"_en"])return n[key+"_en"];
 return n[key] || "";
}
function date(s){
 const d=new Date(s);
 return isNaN(d)?"":d.toLocaleDateString(value==="en"?"en-US":"es-MX",{day:"numeric",month:"short",year:"numeric"})
}
function apply(){
 document.documentElement.lang=value;
 document.title=location.pathname.includes("horoscopos.html")?(value==="en"?"Daily horoscopes | Planeta Actual":"Horóscopos diarios | Planeta Actual"):(value==="en"?"Planeta Actual | World news":"Planeta Actual | Noticias del mundo");
 document.querySelectorAll("[data-i18n]").forEach(e=>e.textContent=get(e.getAttribute("data-i18n")));
 document.querySelectorAll("[data-i18n-placeholder]").forEach(e=>e.placeholder=get(e.getAttribute("data-i18n-placeholder")));
 document.querySelectorAll("[data-i18n-aria]").forEach(e=>e.setAttribute("aria-label",get(e.getAttribute("data-i18n-aria"))));
 const switcher=document.getElementById("pa-language");
 if(switcher){switcher.textContent=value==="en"?"ES / Español":"EN / English";switcher.setAttribute("aria-label",value==="en"?"Cambiar a español":"Switch to English")}
 document.querySelectorAll("[data-horoscope-link]").forEach(a=>a.href="./horoscopos.html"+(value==="en"?"?lang=en":""));
}
window.PA_I18N={
 get language(){return value},get,change,label,newsText,date,apply,
 nextURL:path=>path+(value==="en"?"?lang=en":"")
};
})();