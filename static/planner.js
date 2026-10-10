const dialog = document.querySelector('#activity-dialog');
const form = document.querySelector('#activity-form');
const catalog = [
 ['💻','Lucrez la un proiect de programare','Învățare',45],['📚','Citesc o carte','Învățare',30],['📝','Îmi fac temele','Învățare',60],['🎓','Urmăresc un curs online','Învățare',45],['🗣️','Exersez o limbă străină','Învățare',20],['🧠','Rezolv probleme de logică','Învățare',20],['💻','Învăț ceva nou în IT','Învățare',30],['📝','Recapitulez pentru un examen','Învățare',45],
 ['🏃','Ies la alergat','Mișcare',30],['🚶','Fac o plimbare','Mișcare',30],['🏋️','Merg la sală','Mișcare',60],['🚴','Mă plimb cu bicicleta','Mișcare',45],['🧘','Fac stretching','Mișcare',15],['🏊','Merg la înot','Mișcare',45],['⚽','Joc fotbal cu prietenii','Mișcare',60],['🎵','Dansez pe muzica preferată','Mișcare',20],
 ['🎨','Desenez sau pictez','Hobby',45],['🎸','Exersez la un instrument','Hobby',30],['📷','Ies să fac fotografii','Hobby',45],['🍳','Încerc o rețetă nouă','Hobby',60],['🌱','Îngrijesc plantele','Hobby',20],['🎮','Mă joc un joc video','Hobby',45],['🧩','Fac un puzzle','Hobby',30],['📝','Scriu în jurnal','Hobby',15],
 ['🎬','Mă uit la un film','Relaxare',120],['☕','Savurez o cafea fără grabă','Relaxare',20],['🌿','Petrec timp în natură','Relaxare',45],['😴','Iau o pauză de odihnă','Relaxare',20],['🛁','Îmi fac o seară de răsfăț','Relaxare',45],['🎵','Ascult un album preferat','Relaxare',40],['🧘','Meditez câteva minute','Relaxare',10],['📚','Citesc pentru plăcere','Relaxare',30],
 ['🧹','Fac ordine în cameră','Personal',30],['🛒','Fac cumpărăturile','Personal',45],['📅','Îmi planific săptămâna','Personal',20],['💼','Lucrez la un obiectiv personal','Personal',45],['🍎','Pregătesc o masă sănătoasă','Personal',30],['🤝','Mă întâlnesc cu prietenii','Personal',60],['🐾','Ies cu animalul de companie','Personal',30],['❤️','Petrec timp cu familia','Personal',60],['🎯','Îmi organizez prioritățile','Personal',15],['✈️','Planific o excursie','Personal',30]
];
let filter = '';
const search = document.querySelector('#catalog-search');
const list = document.querySelector('#activity-catalog');
const categoryHelp = JSON.parse(document.querySelector('#category-help-data').textContent);
function updatePreview() {
 document.querySelector('#category-help').textContent = categoryHelp[form.elements.category.value] || '';
 document.querySelector('#repeat-days').hidden = !form.elements.recurring.checked;
 document.querySelector('#preview-emoji').textContent = form.elements.emoji.value;
 document.querySelector('#preview-title').textContent = form.elements.activities.value.trim() || 'Ce vrei să faci?';
 document.querySelectorAll('[data-emoji]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.emoji === form.elements.emoji.value)));
}
function choose(emoji, title, category, duration) {
 form.elements.emoji.value = emoji;
 form.elements.activities.value = title;
 form.elements.category.value = category;
 form.elements.duration.value = duration;
 updatePreview();
 renderCatalog();
}
function normalized(text) { return text.toLocaleLowerCase('ro').normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
function renderCatalog() {
 list.replaceChildren();
 const query = normalized(search.value.trim());
 catalog.filter(item => (!filter || item[2] === filter) && normalized(item[1] + ' ' + item[2]).includes(query)).forEach(item => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'catalog-item';
  button.setAttribute('aria-pressed', String(form.elements.activities.value === item[1]));
  const icon = document.createElement('span'); icon.textContent = item[0]; icon.className = 'catalog-emoji';
  const text = document.createElement('span');
  const title = document.createElement('strong'); title.textContent = item[1];
  const detail = document.createElement('small'); detail.textContent = `${item[2]} · ${item[3]} min`;
  text.append(title, detail); button.append(icon, text);
  button.addEventListener('click', () => choose(...item));
  list.append(button);
 });
 document.querySelector('#catalog-empty').hidden = list.children.length > 0;
}
search.addEventListener('input', renderCatalog);
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
 filter = button.dataset.filter;
 document.querySelectorAll('[data-filter]').forEach(b => b.classList.toggle('selected', b === button));
 renderCatalog();
}));
document.querySelectorAll('[data-emoji]').forEach(button => button.addEventListener('click', () => {
 form.elements.emoji.value = button.dataset.emoji; updatePreview();
}));
form.elements.activities.addEventListener('input', () => { updatePreview(); renderCatalog(); });
document.querySelector('#custom-activity').addEventListener('click', () => {
 form.elements.activities.value = ''; updatePreview(); renderCatalog();
 form.elements.activities.focus();
 form.elements.activities.scrollIntoView({block:'center',behavior:'smooth'});
});
document.querySelectorAll('[data-add]').forEach(button => button.addEventListener('click', () => {
 form.reset(); filter = ''; search.value = '';
 document.querySelectorAll('[data-filter]').forEach(b => b.classList.toggle('selected', b.dataset.filter === ''));
 form.elements.day.value = button.dataset.day || 'Monday';
 form.elements.activities.value = button.dataset.title || '';
 form.elements.category.value = button.dataset.category || 'Personal';
 form.elements.duration.value = button.dataset.duration || '30';
 form.elements.emoji.value = {'Învățare':'💻','Mișcare':'🏃','Hobby':'🎨','Relaxare':'🌿','Personal':'🎯'}[button.dataset.category] || '✨';
 setKind('activity'); updateEventDate(); updatePreview(); renderCatalog(); dialog.showModal(); dialog.scrollTop = 0; search.focus();
}));
document.querySelector('#close-dialog').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
 const bounds = dialog.getBoundingClientRect();
 if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
});

form.elements.category.addEventListener('change', updatePreview);
form.elements.recurring.addEventListener('change', updatePreview);

function updateEventDate() {
 const dayIndex = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'].indexOf(form.elements.day.value);
 const chosen = new Date(form.elements.week.value + 'T12:00:00Z');
 chosen.setUTCDate(chosen.getUTCDate() + dayIndex);
 form.elements.event_date.value = chosen.toISOString().slice(0,10);
}
function setKind(kind) {
 const previous = form.elements.kind.value;
 form.elements.kind.value = kind;
 const isSchool = kind === 'school';
 const dated = ['test','homework','project'].includes(kind);
 document.querySelectorAll('[data-kind]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.kind === kind)));
 document.querySelector('.activity-picker').hidden = kind !== 'activity';
 document.querySelector('#school-details').hidden = kind === 'activity';
 form.elements.subject.closest('label').hidden = !dated;
 form.elements.subject.required = dated;
 document.querySelector('#event-date-label').hidden = !dated;
 form.elements.event_date.required = dated;
 form.elements.event_date.disabled = !dated;
 form.elements.day.closest('label').hidden = dated;
 document.querySelector('#duration-label').hidden = isSchool;
 form.elements.duration.required = !isSchool;
 document.querySelector('#end-time-label').hidden = !isSchool;
 form.elements.end_time.required = isSchool;
 document.querySelector('.repeat-settings').hidden = dated;
 if (dated) form.elements.recurring.checked = false;
 if (isSchool) form.elements.recurring.checked = true;
 form.elements.category.closest('label').hidden = kind !== 'activity';
 if (kind !== 'activity') form.elements.category.value = 'Învățare';
 const defaults = {school:['🏫','Școală','08:00'],test:['📝','Test','09:00'],homework:['📚','Temă','08:00'],project:['💻','Proiect','08:00']};
 if (defaults[kind]) {
  form.elements.emoji.value = defaults[kind][0];
  form.elements.activities.value = defaults[kind][1];
  form.elements.time.value = defaults[kind][2];
 } else if (previous !== 'activity') { form.elements.activities.value = ''; form.elements.emoji.value = '✨'; }
 document.querySelector('#kind-help').textContent = {activity:'Alege o activitate din listă sau scrie una proprie.',school:'Setează intervalul în care ești la școală și zilele în care se repetă.',test:'Adaugă materia, data testului și ce ai de pregătit.',homework:'Adaugă tema, materia și data la care trebuie predată.',project:'Adaugă proiectul, materia și termenul de predare.'}[kind];
 document.querySelector('#time-label').textContent = isSchool ? 'De la ora' : (['homework','project'].includes(kind) ? 'Ora de predare' : 'Ora');
 updatePreview();
}
document.querySelectorAll('[data-kind]').forEach(button => button.addEventListener('click', () => setKind(button.dataset.kind)));
form.elements.day.addEventListener('change', updateEventDate);
