"use client";

import {useEffect,useMemo,useState,type FormEvent} from "react";

const API=process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Chapter={
 title:string; topic:string; summary:string; learning_objectives:string[];
 sections:{id:string;title:string;content:string}[];
 clinical_cases:{title:string;scenario:string;questions:string[];discussion:string}[];
 questions:{question:string;options:string[];correct_answer:string;explanation:string}[];
 references:string[]; educational_notice:string;
};

export default function EstudioPage(){
 const [topic,setTopic]=useState("");
 const [level,setLevel]=useState("clinical");
 const [depth,setDepth]=useState("deep");
 const [language,setLanguage]=useState("es");
 const [chapter,setChapter]=useState<Chapter|null>(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const [available,setAvailable]=useState<boolean|null>(null);
 const [showAnswers,setShowAnswers]=useState(false);

 useEffect(()=>{fetch(API+"/study/status").then(r=>r.json()).then(d=>setAvailable(!!d.available)).catch(()=>setAvailable(false));},[]);

 async function generate(e:FormEvent){
  e.preventDefault();
  if(!topic.trim()||busy)return;
  try{
   setBusy(true);setError("");setChapter(null);setShowAnswers(false);
   const response=await fetch(API+"/study/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({topic:topic.trim(),level,depth,language})});
   const body=await response.json();
   if(!response.ok)throw new Error(body.detail||"No se pudo generar el capítulo.");
   setChapter(body);
  }catch(err:any){setError(err.message||"Error de conexión con el servidor.");}
  finally{setBusy(false);}
 }

 const slug=(value:string)=>value.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").replace(/[^a-z0-9]+/g,"-").replace(/(^-|-$)/g,"");
 const sections=chapter?.sections||[];

 return <main className="min-h-screen bg-slate-950 p-5 text-slate-100 md:p-9">
  <div className="mx-auto max-w-7xl space-y-6">
   <header className="flex flex-wrap items-center justify-between gap-3">
    <div><a href="/" className="text-sm text-cyan-300 hover:underline">← Volver a MedReason AI</a><p className="mt-3 text-sm text-cyan-400">Generador académico con IA</p><h1 className="text-3xl font-bold">Estudio por temas</h1><p className="mt-2 max-w-2xl text-sm text-slate-400">Crea capítulos médicos estructurados, con fisiopatología, aplicación clínica, casos y evaluación. No necesitas subir documentos.</p></div>
    <span className="rounded-full border border-slate-700 px-3 py-2 text-xs text-slate-400">Módulo experimental</span>
   </header>

   <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
    <form onSubmit={generate} className="grid gap-4 md:grid-cols-2">
     <label className="text-sm text-slate-300 md:col-span-2">Tema médico
      <textarea required minLength={3} maxLength={180} rows={2} value={topic} onChange={e=>setTopic(e.target.value)} placeholder="Ej.: Insuficiencia cardíaca: fisiopatología, clasificación, diagnóstico y tratamiento" className="mt-2 block w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-base text-white outline-none focus:border-cyan-500"/>
     </label>
     <label className="text-sm text-slate-300">Nivel académico
      <select value={level} onChange={e=>setLevel(e.target.value)} className="mt-2 block w-full rounded-lg bg-slate-800 p-3"><option value="basic">Ciclo básico</option><option value="clinical">Ciclo clínico</option><option value="internship">Internado médico</option></select>
     </label>
     <label className="text-sm text-slate-300">Profundidad
      <select value={depth} onChange={e=>setDepth(e.target.value)} className="mt-2 block w-full rounded-lg bg-slate-800 p-3"><option value="standard">Estándar</option><option value="deep">Profunda · capítulo completo</option></select>
     </label>
     <label className="text-sm text-slate-300">Idioma
      <select value={language} onChange={e=>setLanguage(e.target.value)} className="mt-2 block w-full rounded-lg bg-slate-800 p-3"><option value="es">Español</option><option value="pt">Português</option></select>
     </label>
     <div className="flex items-end"><button disabled={busy||!topic.trim()} className="w-full rounded-lg bg-cyan-700 px-5 py-3 font-semibold hover:bg-cyan-600 disabled:cursor-not-allowed disabled:opacity-50">{busy?"Generando capítulo...":"Crear capítulo de estudio"}</button></div>
    </form>
    {available===false&&<p className="mt-4 rounded-lg border border-amber-800 bg-amber-950/40 p-3 text-sm text-amber-200">El generador todavía no está conectado. El administrador debe configurar LLM_API_KEY en las variables de entorno del backend de Render.</p>}
    {error&&<p className="mt-4 rounded-lg border border-red-900 bg-red-950/40 p-3 text-sm text-red-200">{error}</p>}
    <p className="mt-3 text-xs text-slate-500">La generación requiere conexión a un proveedor de IA configurado en el backend. El contenido es educativo y debe contrastarse con guías clínicas vigentes.</p>
   </section>

   {busy&&<section className="rounded-2xl border border-cyan-900 bg-cyan-950/30 p-5"><p className="font-semibold text-cyan-200">Preparando tu capítulo...</p><p className="mt-1 text-sm text-slate-400">La generación profunda puede tardar un poco. Mantén esta página abierta.</p></section>}

   {chapter&&<div className="space-y-5">
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
     <div className="flex flex-wrap items-center justify-between gap-3"><span className="rounded-full bg-cyan-950 px-3 py-1 text-xs text-cyan-200">Capítulo generado por IA</span><button onClick={()=>window.print()} className="rounded-lg border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800">Imprimir / guardar PDF</button></div>
     <h2 className="mt-4 text-3xl font-bold">{chapter.title||chapter.topic}</h2>
     <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-300">{chapter.summary}</p>
     {!!chapter.learning_objectives?.length&&<div className="mt-5 rounded-xl bg-slate-800/70 p-4"><h3 className="font-semibold text-cyan-200">Objetivos de aprendizaje</h3><ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-300">{chapter.learning_objectives.map((x,i)=><li key={i}>{x}</li>)}</ul></div>}
    </section>

    <div className="grid gap-5 xl:grid-cols-[260px_minmax(0,1fr)]">
     <aside className="h-fit rounded-2xl border border-slate-800 bg-slate-900 p-5 xl:sticky xl:top-5"><h3 className="font-semibold">Índice del capítulo</h3><nav className="mt-3 space-y-2">{sections.map((s,i)=><a key={s.id||i} href={"#section-"+(s.id||slug(s.title))} className="block text-sm leading-5 text-slate-400 hover:text-cyan-300">{i+1}. {s.title}</a>)}<a href="#clinical-cases" className="block text-sm text-slate-400 hover:text-cyan-300">Casos clínicos</a><a href="#self-assessment" className="block text-sm text-slate-400 hover:text-cyan-300">Autoevaluación</a><a href="#references" className="block text-sm text-slate-400 hover:text-cyan-300">Referencias</a></nav></aside>
     <div className="min-w-0 space-y-5">
      {sections.map((s,i)=><article id={"section-"+(s.id||slug(s.title))} key={s.id||i} className="scroll-mt-5 rounded-2xl border border-slate-800 bg-slate-900 p-5"><h3 className="text-xl font-bold text-cyan-200">{i+1}. {s.title}</h3><div className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-300">{s.content}</div></article>)}
      {!!chapter.clinical_cases?.length&&<section id="clinical-cases" className="scroll-mt-5 rounded-2xl border border-slate-800 bg-slate-900 p-5"><h3 className="text-xl font-bold text-cyan-200">Casos clínicos</h3>{chapter.clinical_cases.map((c,i)=><details key={i} className="mt-4 rounded-xl bg-slate-800 p-4"><summary className="cursor-pointer font-semibold">{i+1}. {c.title}</summary><p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-300">{c.scenario}</p>{c.questions?.map((q,j)=><p key={j} className="mt-2 text-sm text-slate-200">{j+1}. {q}</p>)}<div className="mt-4 border-t border-slate-700 pt-3"><b className="text-cyan-200">Discusión razonada</b><p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-300">{c.discussion}</p></div></details>)}</section>}
      {!!chapter.questions?.length&&<section id="self-assessment" className="scroll-mt-5 rounded-2xl border border-slate-800 bg-slate-900 p-5"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="text-xl font-bold text-cyan-200">Autoevaluación</h3><button onClick={()=>setShowAnswers(v=>!v)} className="rounded-lg bg-slate-800 px-3 py-2 text-sm">{showAnswers?"Ocultar respuestas":"Mostrar respuestas"}</button></div>{chapter.questions.map((q,i)=><div key={i} className="mt-5 border-b border-slate-800 pb-4"><p className="font-semibold">{i+1}. {q.question}</p><ul className="mt-2 space-y-1 pl-4 text-sm text-slate-300">{q.options?.map((o,j)=><li key={j}>{o}</li>)}</ul>{showAnswers&&<div className="mt-3 rounded-lg bg-emerald-950/30 p-3 text-sm"><b className="text-emerald-300">Respuesta: {q.correct_answer}</b><p className="mt-1 whitespace-pre-wrap text-slate-300">{q.explanation}</p></div>}</div>)}</section>}
      {!!chapter.references?.length&&<section id="references" className="scroll-mt-5 rounded-2xl border border-slate-800 bg-slate-900 p-5"><h3 className="text-xl font-bold text-cyan-200">Referencias y lecturas recomendadas</h3><ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-300">{chapter.references.map((r,i)=><li key={i}>{r}</li>)}</ul></section>}
     </div>
    </div>
    <p className="rounded-xl border border-amber-900 bg-amber-950/30 p-4 text-xs leading-6 text-amber-100">{chapter.educational_notice}</p>
   </div>}
  </div>
 </main>;
}
