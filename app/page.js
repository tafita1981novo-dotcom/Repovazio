"use client";
import { useEffect } from "react";

export default function Home() {
  useEffect(() => {
    window.location.replace("/hub.html");
  }, []);
  return (
    <div style={{background:"#030308",minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center"}}>
      <p style={{color:"#4b5563",fontFamily:"monospace",fontSize:"0.8rem"}}>Redirecionando para hub...</p>
    </div>
  );
}
