"use client";
import {useEffect,useState} from "react";

const API=process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
type Doc={id:string;filename:string;extension:string;discipline:string;topic:string;document_type:string;author:string;year:string;page_count:number;size_bytes:number};

export default function BibliotecaPage(){
 const [docs,setDocs]=useState<Doc[]>([]);\n const [accessToken,setAccessToken]=useState("");
 const [file,setFile]=useState<File|null>(null);
 const [discipline,setDiscipline]=useState("Clínica Médica");
 const [topic,setTopic]=useState("");
 const [kind,setKind]=useState("artículo científico");
 const [author,setAuthor]=useState("");
 const [year,setYear]=useState("");
 const [selected,setSelected]=useState<any>(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const [notice,setNotice]=useState("");

 async function api(path:string,options:any={}){
  const isForm=typeof FormData!=="undefined" && options.body instanceof FormData;
  const headers={...(isForm?{}:{"Content-Type":"application/json"}),"X-Library-Token":accessToken,...(options.headers||{})};
  const response=await fetch(API+path,{...options,headers});
  if(!response.ok){let message="Error de comunicación con la API";try{const body=await response.json();message=body.detail||message}catch{}throw new Error(message)}
  return response.json();
 }
 async function refresh(){const result=await api("/library/documents");setDocs(result.documents||[])}
 useEffect(()=>{refresh().catch(e=>setError(e.message))},[]);
 async function upload(e:React.FormEvent<HTMLFormElement>){
  e.preventDefault();if(!file)return;const formElement=e.currentTarget;
  try{setBusy(true);setError("");setNotice("");const body=new FormData();body.append("file",file);body.append("discipline",discipline);body.append("topic",topic);body.append("document_type",kind);body.append("author",author);body.append("year",year);await api("/library/documents",{method:"POST",body});setFile(null);setTopic("");setAuthor("");setYear("");formElement.reset();await refresh();setNotice("Documento añadido correctamente.")}
  catch(err:any){setError(err.message)}finally{setBusy(false)}
 }
 async function read(id:string){try{setBusy(true);setError("");setSelected(await api("/library/documents/"+id))}catch(e:any){setError(e.message)}finally{setBusy(false)}}
 async function remove(id:string){if(!window.confirm("¿Eliminar este documento de la biblioteca?"))return;try{await api("/library/documents/"+id,{method:"DELETE"});if(selected?.id===id)setSelected(null);await refresh();setNotice("Documento eliminado.")}catch(e:any){setError(e.message)}}
 const panel="rounded-2xl border border-slate-800 bg-slate-900 p-5";
 return <main className="min-h-screen bg-slate-950 p-5 text-slate-100 md:p-9"><div className="mx-auto max-w-6xl space-y-5">
  <header className="flex flex-wrap items-center justify-between gap-3"><div><a href="/" className="text-sm text-cyan-300 hover:underline">← Volver a MedReason AI</a><p className="mt-3 text-sm text-cyan-400">Medical Knowledge Base</p><h1 className="text-3xl font-bold">Biblioteca médica</h1><p className="mt-2 text-sm text-slate-400">Gestiona artículos, libros, capítulos y materiales PDF o DOCX.</p></div><span className="rounded-full bg-cyan-950 px-3 py-2 text-sm text-cyan-300">{docs.length} documento(s)</span></header>
  {error&&<div className="rounded-lg border border-red-900 bg-red-950/40 p-3 text-sm text-red-200">{error}</div>}
  {notice&&<div className="rounded-lg border border-emerald-900 bg-emerald-950/30 p-3 text-sm text-emerald-200">{notice}</div>}
  <section className={panel}><h2 className="text-xl font-semibold">Acceso privado</h2><p className="mt-1 text-sm text-slate-400">Introduce la clave configurada en el backend de Render (LIBRARY_ADMIN_TOKEN). No la compartas.</p><input type="password" value={accessToken} onChange={e=>setAccessToken(e.target.value)} placeholder="Clave de acceso de la biblioteca" className="mt-3 block w-full rounded-lg bg-slate-800 p-3 md:max-w-xl"/></section>\n  <section className={panel}><h2 className="text-xl font-semibold">Añadir documento</h2><form onSubmit={upload} className="mt-4 grid gap-4 md:grid-cols-2">
   <label className="text-sm text-slate-300 md:col-span-2">Archivo PDF o DOCX · máximo 30 MB<input required type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={e=>setFile(e.target.files?.[0]||null)} className="mt-2 block w-full rounded-lg border border-slate-700 bg-slate-800 p-3"/></label>
   <label className="text-sm text-slate-300">Disciplina<input required minLength={2} maxLength={80} value={discipline} onChange={e=>setDiscipline(e.target.value)} className="mt-1 block w-full rounded-lg bg-slate-800 p-3"/></label>
   <label className="text-sm text-slate-300">Tema<input maxLength={120} value={topic} onChange={e=>setTopic(e.target.value)} placeholder="Ej.: Síndrome coronario agudo" className="mt-1 block w-full rounded-lg bg-slate-800 p-3"/></label>
   <label className="text-sm text-slate-300">Tipo de material<select value={kind} onChange={e=>setKind(e.target.value)} className="mt-1 block w-full rounded-lg bg-slate-800 p-3"><option>artículo científico</option><option>libro</option><option>capítulo</option><option>guía clínica</option><option>material didáctico</option><option>apuntes</option></select></label>
   <label className="text-sm text-slate-300">Autor / institución<input maxLength={160} value={author} onChange={e=>setAuthor(e.target.value)} className="mt-1 block w-full rounded-lg bg-slate-800 p-3"/></label>
   <label className="text-sm text-slate-300">Año<input maxLength={4} value={year} onChange={e=>setYear(e.target.value)} placeholder="2025" className="mt-1 block w-full rounded-lg bg-slate-800 p-3"/></label>
   <div className="flex items-end"><button disabled={!file||!accessToken.trim()||busy} className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold disabled:opacity-50">{busy?"Procesando...":"Subir documento"}</button></div>
  </form><p className="mt-3 text-xs text-slate-500">Se extrae el texto para consulta. Los PDF escaneados pueden requerir OCR, que todavía no está integrado.</p></section>
  {selected&&<section className={panel}><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold">{selected.filename}</h2><p className="text-xs text-slate-400">{selected.discipline} · {selected.topic||"Sin tema"} · {selected.page_count} páginas/unidades</p></div><button onClick={()=>setSelected(null)} className="rounded-lg bg-slate-800 px-3 py-2 text-sm">Cerrar</button></div><article className="mt-4 max-h-[650px] overflow-auto whitespace-pre-wrap rounded-xl bg-slate-950 p-4 text-sm leading-7 text-slate-300">{selected.content||"No se extrajo texto de este documento."}</article></section>}
  <section className={panel}><div className="flex items-center justify-between gap-3"><h2 className="text-xl font-semibold">Documentos almacenados</h2><button onClick={()=>refresh().catch(e=>setError(e.message))} className="rounded-lg bg-slate-800 px-3 py-2 text-sm">Actualizar</button></div>
   {docs.length===0?<p className="mt-4 text-sm text-slate-400">Aún no hay documentos cargados.</p>:<div className="mt-4 grid gap-3 md:grid-cols-2">{docs.map(doc=><div key={doc.id} className="rounded-xl border border-slate-800 bg-slate-800/60 p-4"><div className="flex items-start justify-between gap-2"><div className="min-w-0 break-words font-semibold">{doc.filename}<p className="mt-1 text-xs font-normal text-cyan-300">{doc.extension.toUpperCase()} · {doc.discipline}</p></div><span className="rounded bg-slate-700 px-2 py-1 text-xs">{doc.page_count} pág.</span></div><p className="mt-2 text-sm text-slate-400">{doc.topic||"Tema no especificado"} · {doc.document_type}</p><p className="mt-1 text-xs text-slate-500">{doc.author||"Autor no indicado"} {doc.year?"· "+doc.year:""}</p><div className="mt-4 flex gap-2"><button disabled={busy} onClick={()=>read(doc.id)} className="rounded-lg bg-cyan-800 px-3 py-2 text-sm disabled:opacity-50">Leer texto</button><button onClick={()=>remove(doc.id)} className="rounded-lg border border-red-900 px-3 py-2 text-sm text-red-300">Eliminar</button></div></div>)}</div>}
  </section>
 </div></main>;
}
