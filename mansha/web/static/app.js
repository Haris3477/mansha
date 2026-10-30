const form = document.querySelector('#check-form');
const message = document.querySelector('#message');
const runButton = document.querySelector('#run');
const error = document.querySelector('#error');
let sample = null;
let running = false;
function selectSample(name) {
  sample = name;
  document.querySelector('#selected').textContent = name ? `Selected sample: ${name}` : '';
}
message.addEventListener('input', () => selectSample(null));
for (const input of form.querySelectorAll('input[type=file]')) {
  input.addEventListener('change', () => selectSample(null));
}
fetch('/api/samples').then(response => response.json()).then(samples => {
  for (const item of samples) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = item.name + (item.has_bom ? ' (with bill of materials)' : '');
    button.addEventListener('click', () => {
      if (running) return;
      message.value = item.message;
      for (const input of form.querySelectorAll('input[type=file]')) input.value = '';
      selectSample(item.name);
    });
    document.querySelector('#samples').append(button);
  }
}).catch(() => { error.textContent = 'Could not load samples.'; });
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (running) return;
  running = true;
  runButton.disabled = true;
  error.textContent = '';
  document.querySelector('#phases').replaceChildren();
  document.querySelector('#result').hidden = true;
  let stream;
  const finish = () => { running = false; runButton.disabled = false; if (stream) stream.close(); };
  try {
    const data = new FormData(form);
    for (const input of form.querySelectorAll('input[type=file]')) {
      if (!input.files.length) data.delete(input.name);
    }
    if (sample) data.set('sample', sample);
    const response = await fetch('/api/run', { method: 'POST', body: data });
    const body = await response.json();
    if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Could not start check.');
    const url = `/api/run/${body.run_id}`;
    stream = new EventSource(`${url}/events`);
    stream.addEventListener('phase', event => {
      const phase = JSON.parse(event.data);
      const row = document.createElement('li');
      const text = document.createElement('p');
      text.textContent = `${phase.name}: ${phase.status} (${phase.seconds}s) — ${phase.summary}${phase.served_by ? ` — ${phase.served_by}` : ''}`;
      row.append(text);
      if (phase.problems.length || phase.warnings.length) {
        const details = document.createElement('details');
        const summary = document.createElement('summary');
        summary.textContent = 'Problems and warnings';
        const content = document.createElement('p');
        content.textContent = [...phase.problems, ...phase.warnings].join('\n');
        details.append(summary, content);
        row.append(details);
      }
      document.querySelector('#phases').append(row);
    });
    stream.addEventListener('result', event => {
      const result = JSON.parse(event.data);
      document.querySelector('#outcome').textContent = `${result.status}${result.verdict ? ` / ${result.verdict}` : ''} (${result.seconds}s)`;
      const warnings = document.querySelector('#warnings');
      warnings.replaceChildren();
      for (const warning of result.warnings) {
        const li = document.createElement('li'); li.textContent = warning; warnings.append(li);
      }
      const report = document.querySelector('#report');
      report.dir = result.dir; report.lang = result.language;
      report.innerHTML = result.report_html;
      document.querySelector('#download').href = `${url}/report.md`;
      document.querySelector('#result').hidden = false;
      finish();
    });
    stream.addEventListener('error', event => {
      error.textContent = event.data ? JSON.parse(event.data).message : 'Connection interrupted. Please try again.';
      finish();
    });
  } catch (err) { error.textContent = err.message; finish(); }
});
