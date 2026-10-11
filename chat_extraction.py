"""AI interpretation of multi-event scheduling, validated before database writes."""
import json
import re
from datetime import date, timedelta
from urllib import request as http
from chat_planning import normalized, event_date, time_range

WEEKDAYS = ['luni', 'marti', 'miercuri', 'joi', 'vineri', 'sambata', 'duminica']
DAY_NAMES = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică']
RANGE_PATTERN = r'\b(?:de la\s+|intre\s+)?\d{1,2}(?::\d{2})?\s*(?:[-–—]|pana la|la)\s*\d{1,2}(?::\d{2})?\b'
SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'question': {'type': 'string'},
        'events': {'type': 'array', 'maxItems': 20, 'items': {
            'type': 'object', 'additionalProperties': False,
            'properties': {
                'title': {'type': 'string'},
                'days': {'type': 'array', 'items': {'type': 'string', 'enum': WEEKDAYS}},
                'date': {'type': ['string', 'null']},
                'start': {'type': ['string', 'null']},
                'end': {'type': ['string', 'null']},
                'duration': {'type': ['integer', 'null']},
                'recurring': {'type': 'boolean'},
            }, 'required': ['title', 'days', 'date', 'start', 'end', 'duration', 'recurring']
        }}
    }, 'required': ['question', 'events']
}
SCHEMA['properties'] = dict(events=SCHEMA['properties']['events'], question=SCHEMA['properties']['question'])

PROMPT = 'You are a data extraction engine, not a conversational assistant. Extract ALL calendar events explicitly stated in the latest Romanian user message. Return JSON only. Ignore greetings and polite introductory words. Never echo the user\'s question in the question field. question is EMPTY STRING when dates or weekday names and times are present. Return one event object per group of weekdays sharing the same title and hours. Use Romanian weekday identifiers without accents. Weekday names: luni Monday, marti Tuesday, miercuri Wednesday, joi Thursday, vineri Friday, sambata Saturday, duminica Sunday. "de la 8 la 15" means start="08:00", end="15:00". A second list of weekdays after that interval belongs to the following interval. Grouped school hours imply recurring=true. Use title="Școală" for school. duration=null when end exists. date=null when days exists. For other activities use a short title based on the actual activity. Do not create extra events. Ask a short Romanian question only if an essential time or date is missing. Example input: "salut, pune-mi sport marti si joi 17-18, sambata de la 10 la 12". Output: {"events":[{"title":"Sport","days":["marti","joi"],"date":null,"start":"17:00","end":"18:00","duration":null,"recurring":false},{"title":"Sport","days":["sambata"],"date":null,"start":"10:00","end":"12:00","duration":null,"recurring":false}],"question":""}.'


def needs_ai(text):
    plain = normalized(text)
    days = [day for day in WEEKDAYS if re.search(r'\b' + day + r'\b', plain)]
    ranges = re.findall(RANGE_PATTERN, plain)
    if re.search(r'\bam (?:nevoie|o intrebare|probleme|dificultati)\b', plain):
        return False
    scheduling = re.search(r'\b(?:pune|adauga|programeaza|noteaza|salveaza|am|merg|vreau|trebuie)\b', plain)
    if not scheduling:
        return False
    return len(days) > 1 or len(ranges) > 1 or bool(re.search(r'\b(?:vreau sa|trebuie sa|imi poti|poti sa|as vrea|merg la)\b', plain))


def school_groups(text):
    """Independently check the day/range association for grouped school hours."""
    plain = normalized(text)
    if 'scoala' not in plain:
        return None
    ranges = list(re.finditer(RANGE_PATTERN, plain))
    if not ranges:
        return None
    groups = {}
    previous = 0
    for interval in ranges:
        prefix = plain[previous:interval.start()]
        days = [day for day in WEEKDAYS if re.search(r'\b' + day + r'\b', prefix)]
        if not days:
            return None
        clock = time_range(interval.group())
        if not clock or clock.get('error'):
            raise ValueError('Intervalul de școală nu este valid. Care sunt orele de început și de sfârșit?')
        for day in days:
            if day in groups:
                raise ValueError('Ai menționat aceeași zi cu mai multe intervale. Ce program păstrăm pentru acea zi?')
            groups[day] = (clock['time'], clock['duration'])
        previous = interval.end()
    if any(re.search(r'\b' + day + r'\b', plain[previous:]) for day in WEEKDAYS):
        return None
    return groups


def validate(result, text, today, context_date=None):
    if not isinstance(result, dict) or not isinstance(result.get('events'), list) or len(result['events']) > 20:
        raise ValueError('Nu am putut separa activitățile. Spune-mi ce zile au același interval.')
    if result.get('question'):
        return {'error': str(result['question'])[:500]}
    if not result['events']:
        if school_groups(text):
            raise ValueError('Nu am reușit să extrag toate intervalele. Nu am salvat nimic; încearcă din nou mesajul.')
        return None
    plain = normalized(text)
    # Don't turn requests for advice or conditional examples into real entries.
    if not re.search(r'\b(?:pune|adauga|programeaza|noteaza|salveaza|am|merg|vreau|trebuie)\b', plain) or (re.search(r'\b(?:cum|daca)\b', plain) and not re.search(r'\b(?:pune|adauga|programeaza|noteaza|salveaza)\b', plain)):
        return None
    supplied_days = {day for day in WEEKDAYS if re.search(r'\b' + day + r'\b', plain)}
    extracted_days = set()
    drafts = []
    from planner import week_of
    base_week = week_of((today + timedelta(days=1)).isoformat())
    if 'saptamana viitoare' in plain:
        base_week = week_of(today.isoformat()) + timedelta(days=7)
    if 'saptamana asta' in plain or 'saptamana aceasta' in plain:
        base_week = week_of(today.isoformat())
    relative = event_date(text, today) if re.search(r'\b(?:azi|astazi|maine|poimaine)\b', plain) else None
    for event in result['events']:
        if not isinstance(event, dict) or not isinstance(event.get('title'), str) or not 1 <= len(event['title'].strip()) <= 160:
            raise ValueError('Ce activitate vrei să adaug?')
        start, end = event.get('start'), event.get('end')
        valid_time = r'(?:[01]\d|2[0-3]):[0-5]\d'
        if not isinstance(start, str) or not re.fullmatch(valid_time, start):
            raise ValueError('La ce oră începe activitatea?')
        if end is not None:
            if not isinstance(end, str) or not re.fullmatch(valid_time, end):
                raise ValueError('La ce oră se termină activitatea?')
            duration = int(end[:2])*60 + int(end[3:]) - int(start[:2])*60 - int(start[3:])
        else:
            duration = event.get('duration') or 30
        if not isinstance(duration, int) or isinstance(duration, bool) or not 5 <= duration <= 480:
            raise ValueError('Intervalul trebuie să dureze 5–480 minute, cu sfârșitul după început.')
        days = event.get('days')
        if not isinstance(days, list) or len(days) != len(set(days)) or any(day not in supplied_days for day in days):
            raise ValueError('Nu am putut asocia corect zilele. Care sunt zilele pentru fiecare interval?')
        recurring = bool(event.get('recurring'))
        if 'scoala' in plain and len(supplied_days) > 1:
            recurring = not any(word in plain for word in ('doar', 'saptamana asta', 'saptamana aceasta'))
        elif recurring and not re.search(r'\b(?:saptamanal|in fiecare|se repeta|permanent)\b', plain):
            recurring = False
        dates = []
        if days:
            extracted_days.update(days)
            dates = [(base_week + timedelta(days=WEEKDAYS.index(day))).isoformat() for day in days]
        else:
            selected_date = relative or event.get('date') or context_date
            if not selected_date:
                raise ValueError('În ce zi este activitatea?')
            dates = [date.fromisoformat(selected_date).isoformat()]
        for selected_date in dates:
            drafts.append(dict(title=event['title'].strip(), date=selected_date, time=start, duration=duration, recurring=recurring))
    if supplied_days and extracted_days != supplied_days:
        raise ValueError('Nu am reușit să includ toate zilele. Spune-mi ce zile au fiecare interval.')
    expected = school_groups(text)
    if expected:
        actual = {WEEKDAYS[date.fromisoformat(draft['date']).weekday()]: (draft['time'], draft['duration']) for draft in drafts}
        if actual != expected or len(drafts) != len(expected):
            raise ValueError('Nu am asociat sigur intervalele cu zilele. Spune-mi separat zilele cu program până la prima oră și cele cu program până la a doua oră.')
        for draft in drafts:
            draft['title'] = 'Școală'
    keys = [(draft['title'], draft['date'], draft['time']) for draft in drafts]
    if len(keys) != len(set(keys)):
        raise ValueError('Mesajul pare să conțină activități repetate. Ce interval păstrăm?')
    return {'drafts': drafts}


def extract(text, today, model, context_date=None, history=None):
    context = f'Azi este {today.isoformat()}, mâine {(today + timedelta(days=1)).isoformat()}. Ziua discutată anterior: {context_date}. '
    context += '\nSchema JSON: ' + json.dumps(SCHEMA, ensure_ascii=False)
    messages = [{'role': 'system', 'content': PROMPT + context}]
    # Interpret the explicit request in isolation: older erroneous summaries must not override it.
    messages.append({'role': 'user', 'content': text})
    payload = dict(model=model, messages=messages, stream=False, format=SCHEMA, options=dict(temperature=0, num_predict=1800, num_ctx=8192))
    req = http.Request('http://127.0.0.1:11434/api/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with http.urlopen(req, timeout=180) as response:
        result = json.loads(json.load(response)['message']['content'])
    return validate(result, text, today, context_date)
