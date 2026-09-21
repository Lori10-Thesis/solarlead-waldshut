"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, ApiError } from '@/lib/api';

export default function AdminLogin(){
  const router=useRouter();
  const [email,setEmail]=useState('admin@example.com');
  const [password,setPassword]=useState('');
  const [error,setError]=useState('');

  const submit=async(e:React.FormEvent)=>{
    e.preventDefault();
    setError('');
    try{
      await api('/api/auth/login',{method:'POST',body:JSON.stringify({email:email.trim(),password})});
      router.push('/admin');
      router.refresh();
    }catch(err){
      if(err instanceof ApiError){
        if(err.status===401) setError('E-Mail oder Passwort ist falsch.');
        else if(err.status===422) setError('Die Login-Daten haben ein ungültiges Format.');
        else setError(`Login fehlgeschlagen (HTTP ${err.status}).`);
      }else{
        setError('Backend nicht erreichbar oder Netzwerkfehler.');
      }
    }
  };

  return <div className="container auth-shell"><form className="card auth-card" onSubmit={submit}>
    <div className="brand">Solar<span>Lead</span></div><h2>Vertriebslogin</h2><p>Geschützter Zugang zum Lead Command Center.</p>
    <div className="field"><label>E-Mail</label><input type="email" autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)}/></div>
    <div className="field"><label>Passwort</label><input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)}/></div>
    <button className="btn">Anmelden</button>{error&&<div className="error">{error}</div>}
  </form></div>;
}
