"""CN HCC Alba, grade X theoretical, 2026–2027.
National dates: https://legislatie.just.ro/Public/DetaliiDocument/307408
Alba break: https://alba24.ro/calendar-an-scolar-2026-2027-perioadele-de-cursuri-vacante-si-zile-libere-pentru-elevi-si-profesori-noutati-la-inceputul-scolii-1156031.html
School-specific alternative and green weeks are not yet verified.
"""
from datetime import date, timedelta
BREAKS = [('2026-10-24','2026-11-01'),('2026-12-23','2027-01-10'),('2027-03-01','2027-03-07'),('2027-04-24','2027-05-04')]
def school_day(day):
    return date(2026,9,7)<=day<=date(2027,6,18) and day.weekday()<5 and day.isoformat() not in {'2026-10-05','2026-11-30','2026-12-01','2027-06-01'} and not any(a<=day.isoformat()<=b for a,b in BREAKS)
def visible(row, week, days):
    return not (row['kind']=='school' and row['recurring']) or (row['day'] in days and school_day(week+timedelta(days=days.index(row['day']))))
