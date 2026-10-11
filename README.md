# Task-Project

Planificator local, fără autentificare, cu orar permanent, teste, teme, proiecte și chat AI. Aplicația ascultă doar pe 127.0.0.1. La prima deschidere păstrează profilul conectat anterior sau profilul cu cele mai multe activități; celelalte date existente rămân în baza de date. Toate deschiderile ulterioare folosesc același profil local.

## Instalare și pornire

Ai nevoie de Python 3.10 sau mai nou.

1. Descarcă proiectul de pe GitHub (Code → Download ZIP) și dezarhivează-l, sau clonează repository-ul.
2. Deschide un terminal în folderul proiectului și rulează:

```sh
python -m venv .venv
```

Pe Windows:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Pe macOS / Linux:

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

3. Deschide http://127.0.0.1:5000 în browser. Nu trebuie să creezi un cont.

Baza de date se creează automat la prima deschidere. Fiecare instalare are propriul program. Aplicația folosește Ollama pentru chat local, fără cheie API sau costuri pe mesaje. Pentru a opri aplicația, apasă Ctrl+C în terminal.

## Chat local cu Ollama

Instalează Ollama de la https://ollama.com sau, pe macOS, cu Homebrew:

```sh
brew install ollama
brew services start ollama
ollama pull gemma3:4b
```

Chatul folosește serverul local de pe `127.0.0.1:11434`. Mesajele și programul săptămânii sunt procesate pe computer, fără apeluri către OpenAI. Prima cerere poate dura mai mult pentru încărcarea modelului. Modelul se descarcă o singură dată și ocupă aproximativ 3,4 GB.

Opțional, setează `OLLAMA_MODEL` în `.env` pentru un alt model local instalat. Fișierul `.env` este exclus din Git. Istoricul conversației și activitățile incomplete se păstrează în baza de date locală, inclusiv după repornire. «Conversație nouă» șterge istoricul conversației, fără să șteargă activitățile. Chatul poate pregăti activități din mesaje precum «Mâine am test la matematică la ora 10». Dacă lipsește ziua sau ora, le cere în conversație. Activitățile complete se salvează direct și calendarul se actualizează fără reîncărcare. Intervalele precum «8–9 istorie» devin o singură activitate de 60 de minute. Repetarea aceleiași activități la aceeași dată și oră actualizează intrarea existentă. Datele relative sunt calculate în Europe/Bucharest, independent de săptămâna afișată.

Mesajele cu mai multe zile și intervale sunt interpretate de Ollama într-o structură verificată înainte de salvare. Orarul de școală cu mai multe zile se salvează săptămânal; poți preciza «doar săptămâna asta» pentru intrări temporare. Dacă modelul omite o zi sau asociază greșit intervalele explicite ale școlii, nu se salvează un orar parțial.

### Orar din fotografie

În chat, „📷 Adaugă orarul din poză” importă un JPG/PNG/WebP (max. 8 MB). Fotografia trebuie să conțină zilele, materiile și intervalele orare. Dacă poza are numai numerele orelor, scrie intervalele în mesaj înainte să selectezi poza. Citirea folosește local macOS Vision și Qwen 2.5 7B; Gemma 3 oferă alternativa vizuală dacă OCR nu este disponibil. Qwen trebuie instalat în Ollama (`ollama pull qwen2.5:7b`). Recunoașterea macOS necesită Command Line Tools, cu SDK 15.4 în această instalare.

Un import complet înlocuiește blocurile generice „Școală” și orarul importat anterior, păstrând testele, temele și activitățile personale. Versiunea anterioară este păstrată în SQLite în `TIMETABLE_BACKUPS`. Fotografia nu este păstrată. Orele recurente sunt afișate numai în zilele de curs pentru Alba, clasa a X-a, profil teoretic, anul 2026–2027. Calendarul trebuie actualizat pentru anul următor. Datele locale pentru Școala altfel, Săptămâna verde și eventuale suspendări nu sunt încă disponibile.
