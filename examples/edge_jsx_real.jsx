import React, { useState } from 'react';

export default function Hero() {
  const [nombre, setNombre] = useState('Marta');
  const [rol] = useState('Diseñadora front-end');

  return (
    <section id="hero" className="hero">
      <h1>Hola soy {nombre}, {rol}</h1>
      <p>Trabajo en productos fintech con foco en accesibilidad y design tokens.</p>
      <a href="#trabajos">Ver mis trabajos</a>
      <button onClick={() => setNombre('Marta Gómez')}>Mostrar nombre completo</button>
    </section>
  );
}
