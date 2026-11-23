'use strict';

const API = document.querySelector('meta[name=api]')?.content ?? '';
const MESSAGES = {
  400: 'Please check your question.',
  413: 'Your question is too long.',
  502: 'The assistant is unavailable, try again later.',
  504: 'The assistant took too long, try again.'
};
const $ = id => document.getElementById(id);

$('f').addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = $('q').value.trim();
  if (!question) return;
  $('go').disabled = true;
  $('f').setAttribute('aria-busy', 'true');
  $('status').textContent = 'Thinking...';
  $('answer').textContent = '';

  try {
    const r = await fetch(API + '/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
      signal: AbortSignal.timeout(70000)
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(MESSAGES[r.status] || data.error || 'Unexpected error (' + r.status + ')');
    $('answer').textContent = data.answer;
    $('status').textContent = '';
    $('answer').focus();
  } catch (err) {
    $('status').textContent = err.name === 'TimeoutError' ? 'No answer received, try again.' : err.name === 'TypeError' ? 'Cannot reach the assistant.' : err.message;
  } finally {
    $('go').disabled = false;
    $('f').removeAttribute('aria-busy');
  }
});
