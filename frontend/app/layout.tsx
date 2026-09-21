import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";

const siteUrl=process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
export const metadata={
  metadataBase:new URL(siteUrl),
  title:{default:"SolarLead",template:"%s | SolarLead"},
  description:"Balkon-PV Potenzial kostenlos prüfen und passende regionale Angebote anfragen.",
  robots:{index:true,follow:true},
};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="de"><body>{children}</body></html>}
