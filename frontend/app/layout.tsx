import "./globals.css";
import RegisterSW from "./register-sw";
export const metadata={title:"MedReason AI",description:"Clinical reasoning and medical learning platform",manifest:"/manifest.webmanifest"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="es"><body><RegisterSW/>{children}</body></html>}
