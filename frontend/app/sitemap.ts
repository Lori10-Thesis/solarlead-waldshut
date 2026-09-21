import type { MetadataRoute } from 'next';
export default function sitemap(): MetadataRoute.Sitemap {
  const base=(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/$/,'');
  return [
    {url:`${base}/`,changeFrequency:'weekly',priority:1},
    {url:`${base}/impressum`,changeFrequency:'yearly',priority:.2},
    {url:`${base}/datenschutz`,changeFrequency:'yearly',priority:.2},
  ];
}
