"""Resolve Romanian dates and prepare explicitly reviewed planner entries."""
from datetime import date, datetime, timedelta
import re
import unicodedata
from zoneinfo import ZoneInfo


def today_local():
    return datetime.now(ZoneInfo('Europe/Bucharest')).date()


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(c))


def event_date(text, today):
    text = normalized(text)
    for name, offset in [('poimaine', 2), ('maine', 1), ('azi', 0), ('astazi', 0)]:
        if re.search(r'\b' + name + r'\b', text):
            return (today + timedelta(days=offset)).isoformat()
    match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if match:
        try:
            return date.fromisoformat(match[1]).isoformat()
        except ValueError:
            return None
    match = re.search(r'\b(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?\b', text)
    if match:
        try:
            return date(int(match[3] or today.year), int(match[2]), int(match[1])).isoformat()
        except ValueError:
            return None
    for weekday, name in enumerate(['luni', 'marti', 'miercuri', 'joi', 'vineri', 'sambata', 'duminica']):
        if re.search(r'\b' + name + r'\b', text):
            offset = (weekday - today.weekday()) % 7
            if 'viitoare' in text:
                offset = 7 - today.weekday() + weekday
            return (today + timedelta(days=offset)).isoformat()
    return None


def event_time(text):
    match = re.search(r'\b(?:la(?:\s+ora)?|ora)\s+(\d{1,2})(?:[:.](\d{2}))?\b|\b(\d{1,2}):(\d{2})\b', normalized(text))
    if not match:
        match = re.fullmatch(r'\s*(\d{1,2})(?:[:.](\d{2}))?\s*', text)
    if match:
        groups = match.groups()
        hour = int(groups[0] or groups[2]) if len(groups) == 4 else int(groups[0])
        minute = int((groups[1] or groups[3] or '0') if len(groups) == 4 else (groups[1] or '0'))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f'{hour:02d}:{minute:02d}'
    return None


def time_range(text):
    match = re.search(r"\b(?:de la\s+|intre\s+)?(\d{1,2})(?::(\d{2}))?\s*(?:[-–—]|pana la|la)\s*(\d{1,2})(?::(\d{2}))?\b", re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "", normalized(text)))
    if not match:
        return None
    h1, m1, h2, m2 = int(match[1]), int(match[2] or 0), int(match[3]), int(match[4] or 0)
    duration = h2 * 60 + m2 - h1 * 60 - m1
    if h1 > 23 or h2 > 23 or m1 > 59 or m2 > 59 or not 5 <= duration <= 480:
        return {'error': 'Intervalul trebuie să aibă ora de sfârșit după ora de început și o durată de 5–480 minute.'}
    return {'time': f'{h1:02d}:{m1:02d}', 'duration': duration}


def clean_title(text):
    text = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', text)
    title = re.sub(r'(?i)\b(?:de la\s+|între\s+|intre\s+)?\d{1,2}(?::\d{2})?\s*(?:[-–—]|până la|pana la|la)\s*\d{1,2}(?::\d{2})?\b', '', text)
    title = re.sub(r'(?i)\b(?:azi|astăzi|astazi|mâine|maine|poimâine|poimaine|luni|marți|marti|miercuri|joi|vineri|sâmbătă|sambata|duminică|duminica)\b', '', title)
    title = re.sub(r'(?i)\b(?:la(?:\s+ora)?|ora)\s+\d{1,2}(?:[:.]\d{2})?\b|\b\d{1,2}:\d{2}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[./]\d{1,2}(?:[./]\d{4})?\b', '', title)
    title = re.sub(r'(?i)\b(?:pentru|timp de|durata(?: de)?)?\s*\d+\s*(?:minute|min|ore|oră|ora)\b', '', title)
    title = re.sub(r'(?i)^(?:(?:te rog|în plan|in plan|în program|in program|că|ca|o|un|de la|la|de)\s+)+', '', title.strip())
    return re.sub(r'\s+', ' ', title).strip(' ,.!')


def plan_message(text, pending, today, context_date=None):
    plain = normalized(text)
    if re.search(r'\b(?:anuleaza|renunta)\b', plain):
        return {'cancelled': True} if pending else None
    if re.search(r"\bam (?:nevoie|o intrebare|probleme|dificultati)\b", plain):
        return None
    intent = re.search(r'\b(?:am|adauga|pune|programeaza|noteaza|salveaza)\b', plain)
    explicit = re.search(r'\b(?:adauga|pune|programeaza|noteaza|salveaza)\b', plain)
    if not explicit and ('?' in text or re.match(r'\s*(?:cum|ce|cand|de ce|pot|poti|daca)\b', plain)):
        return None
    resolved = event_date(text, today)
    interval = time_range(text)
    clock = event_time(text)
    duration = re.search(r'\b(\d+)\s*(minute|min|ore|ora)\b', plain)
    remainder = clean_title(text[intent.end():] if intent else text)
    # A time range plus a subject is also an event statement: "8–9 istorie".
    if not intent and not pending and not (interval and remainder):
        return None
    if pending and not intent and not any((resolved, interval, clock, duration)):
        return None
    if interval and interval.get('error'):
        return interval
    draft = dict(pending or {})
    if remainder and (intent or (interval and not pending)):
        draft = {'title': remainder[:160], 'duration': 30}
        if not resolved and context_date:
            draft['date'] = context_date
    if resolved:
        draft['date'] = resolved
    if interval:
        draft.update(interval)
    elif clock:
        draft['time'] = clock
    if duration and not interval:
        minutes = int(duration[1]) * (60 if duration[2] in ('ora', 'ore') else 1)
        if not 5 <= minutes <= 480:
            return {'error': 'Durata trebuie să fie între 5 și 480 de minute.'}
        draft['duration'] = minutes
    if not draft.get('title'):
        return {'error': 'Ce activitate vrei să pun în plan? De exemplu: „Mâine am istorie de la 8 la 9”.'}
    draft['title'] = draft['title'][0].upper() + draft['title'][1:]
    missing = [name for name in ('date', 'time') if not draft.get(name)]
    return {'draft': draft, 'missing': missing}
