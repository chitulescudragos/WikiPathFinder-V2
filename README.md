# WikiPathFinder

WikiPathFinder este o aplicație web dezvoltată pentru explorarea și vizualizarea grafurilor de cunoaștere bazate pe Wikipedia. Aplicația permite identificarea celui mai scurt drum între două pagini Wikipedia, folosind algoritmi de căutare avansați și generând reprezentări vizuale interactive.

## Descriere Proiect
Proiectul a fost creat cu scopul de a facilita înțelegerea conexiunilor dintre concepte diferite, pornind de la teoria "celor 6 grade de separare". Utilizatorul introduce o pagină de start și una de destinație, iar sistemul generează un traseu optim și vizualizează contextul acestuia sub formă de graf ierarhic.

## Funcționalități
- Căutare bidirecțională: Algoritm BFS (Breadth-First Search) eficient pentru găsirea drumului minim.
- Vizualizare interactivă: Generarea de grafuri folosind PyVis și Vis.js.
- Istoric: Salvarea căutărilor anterioare pentru acces rapid.
- Interfață responsivă: Design adaptabil pentru desktop și mobil.

## Tehnologii Utilizate
- Backend: Python (Flask)
- Frontend: HTML5, CSS3 (Bootstrap 5)
- Vizualizare: PyVis / Vis.js
- API: Wikipedia Action API

## Instalare și Rulare
1. Asigură-te că ai Python instalat.
2. Instalează dependințele necesare:
   pip install flask requests pyvis
3. Rulează aplicația:
   python app.py
4. Accesează http://127.0.0.1:5000 în browser.

## Resurse Externe și Biblioteci
În realizarea acestui proiect au fost utilizate următoarele resurse externe:
- Framework Web: Flask (Open Source)
- Frontend: Bootstrap 5 (CDN utilizat pentru stilizare)
- Vizualizare Grafuri: Vis.js / PyVis (Bibliotecă pentru redarea rețelelor)
- Date: Wikipedia Action API (Pentru interogarea datelor publice Wikipedia)

## Declarație de Proprietate Intelectuală
Prin prezenta, declar următoarele:
- Logica algoritmului de căutare (BFS bidirecțional) și arhitectura aplicației au fost dezvoltate integral de către autorul proiectului.
- Bibliotecile menționate în secțiunea "Resurse Externe" sunt utilizate conform licențelor lor standard (Open Source/MIT).
- Nu au fost utilizate fragmente de cod sau active grafice care să încalce drepturile de autor.

## Autori
Nume și Prenume: Chitulescu Dragos-Mihai
Instituția: Colegiul National "Constantin Carabella"
---
Proiect realizat pentru Concursul InfoEducație, 2026.