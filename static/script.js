async function fetchEvents() {
  try {
    const res = await fetch("/events/latest");
    const data = await res.json();

    const container = document.getElementById("events");
    container.innerHTML = "";

    data.forEach(event => {
      const div = document.createElement("div");
      div.className = "event";

      const date = new Date(event.timestamp);
      const formattedTime = date.toUTCString().replace("GMT", "UTC");

      let message = "";
      if (event.event_type === "push") {
        message = `"${event.author}" pushed to "${event.to_branch}" on ${formattedTime}`;
      } else if (event.event_type === "pull_request") {
        message = `"${event.author}" submitted a pull request from "${event.from_branch}" to "${event.to_branch}" on ${formattedTime}`;
      } else if (event.event_type === "merge") {
        message = `"${event.author}" merged branch "${event.from_branch}" to "${event.to_branch}" on ${formattedTime}`;
      } else {
        message = `Unknown event by "${event.author}" on ${formattedTime}`;
      }

      div.innerText = message;
      container.appendChild(div);
    });

  } catch (err) {
    console.error("Error fetching events:", err);
  }
}

// Call every 15 seconds
fetchEvents();
setInterval(fetchEvents, 15000);
