export const API = process.env.NEXT_PUBLIC_API_URL ?? "";

export class ApiError extends Error { constructor(public status:number,message:string){super(message);} }
function csrfToken(){
  if(typeof document==='undefined') return '';
  return document.cookie.split('; ').find(v=>v.startsWith('solarlead_csrf='))?.split('=')[1] || '';
}
export async function api<T>(path:string,options?:RequestInit):Promise<T>{
  const method=(options?.method || 'GET').toUpperCase();
  const headers:Record<string,string>={"Content-Type":"application/json",...((options?.headers as Record<string,string>)||{})};
  if(['POST','PUT','PATCH','DELETE'].includes(method) && (path.startsWith('/api/admin') || path === '/api/auth/logout')) headers['X-CSRF-Token']=decodeURIComponent(csrfToken());
  const r=await fetch(`${API}${path}`,{...options,headers,credentials:'include',cache:'no-store'});
  if(!r.ok) throw new ApiError(r.status,await r.text());
  return r.json();
}
