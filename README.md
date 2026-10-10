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

Baza de date se creează automat la prima deschidere. Fiecare instalare are propriul program. Aplicația funcționează fără cheie API pentru toate funcțiile de planificare; cheia este necesară numai pentru chat. Pentru a opri aplicația, apasă Ctrl+C în terminal.

## Activarea chatului OpenAI

1. Creează o cheie API în contul OpenAI Platform și configurează creditul/facturarea API.
2. Copiază `.env.example` într-un fișier `.env` din acest director.
3. Completează `OPENAI_API_KEY` în `.env`, local. Nu trimite cheia în chat și nu o pune în HTML sau JavaScript.
4. `OPENAI_MODEL` stabilește modelul folosit. Implicit: `gpt-6-astra`; modelul trebuie să fie disponibil contului tău.
5. Deschide aplicația și trimite un mesaj. Configurarea din `.env` este citită la fiecare cerere, deci schimbarea cheii nu cere repornire.

Fișierul `.env` este exclus din Git. Variabilele de mediu cu aceleași nume au prioritate.
Chatul transmite mesajele, ultimele schimburi din conversație și programul utilizatorului pentru săptămâna afișată către OpenAI. Istoricul rămâne doar în pagina deschisă și se pierde la reîncărcare. Chatul propune planuri; nu modifică activitățile. Integrarea folosește Responses API cu `store: false`, fără a promite că aceasta elimină toate formele de păstrare a datelor de către furnizor.

Documentație: https://developers.openai.com/api/docs/quickstart
