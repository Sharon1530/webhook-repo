function fetchEvents() {
  fetch('/events/latest')
    .then(res => res.json())
    .then(events => {
      const list = document.getElementById('event-list');
      list.innerHTML = ''; // Clear existing
      events.forEach(evt => {
        const li = document.createElement('li');
        li.textContent = evt.text + (evt.summary ? ` — ${evt.summary}` : '');
        list.appendChild(li);
      });
    });
}

// Poll every 15s
fetchEvents();
setInterval(fetchEvents, 15000);
