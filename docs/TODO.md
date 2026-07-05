  • P0 — Bloqueante (Indexación/Rastreo):
      • Incluir la URL  /tienda/  dentro del listado dinámico del generador app.py en  app.py .
  • P1 — Alto Impacto (Arquitectura de rastreo):
      • Envolver la etiqueta de indexación en  head.html  dentro de un bloque Jinja2 configurable (ej:  {% block meta_robots %} ) y sobrescribirlo en carrito.html a  noindex, nofollow 
      para evitar la indexación de páginas privadas y transaccionales.
  • P2 — Medio Impacto (Enriquecimiento SERP):
      • Añadir marcado JSON-LD dinámico de  ItemList  o  Product  en la página de catálogo de cada tenant para que Google extraiga los productos de la grilla directamente en la página de
      resultados de búsqueda.
  • P3 — Bajo Impacto (Optimización de velocidad):
      • Añadir  loading="lazy"  al elemento  <img>  de la tarjeta de producto en  tienda.html  para reducir la transferencia inicial de datos.

