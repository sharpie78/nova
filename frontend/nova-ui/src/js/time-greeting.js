let isGreetingUpdated = false;  // Flag to track if the greeting has been updated

function updateTime() {
  // Get the current time
  const now = new Date();
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const seconds = now.getSeconds();

  // Get the day, date, and month
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  const formattedDate = now.toLocaleDateString('en-GB', options);  // Format as "Tuesday 16th March 2025"

  // Format the time as HH:MM:SS (24-hour format)
  const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

  // Set the time in the timestamp element
  document.getElementById('time').textContent = formattedDate + ' - ' + formattedTime;
}

function updateGreeting(username) {
  // Get the current hour to determine the greeting
  const now = new Date();
  const hours = now.getHours();
  let greeting = '';

  if (hours >= 2 && hours < 12) {
    greeting = `Good morning, ${username}`;
  } else if (hours >= 12 && hours < 18) {
    greeting = `Good afternoon, ${username}`;
  } else {
    greeting = `Good evening, ${username}`;
  }

  // Set the greeting in the HTML
  const greetingElement = document.getElementById('greeting');
  if (greetingElement && username) {
    greetingElement.textContent = greeting;
  }
}

function fetchUsernameAndUpdateGreeting() {
  // Fetch the username directly from localStorage
  const username = localStorage.getItem("username");

  // Check if username exists and update the greeting
  if (username && !isGreetingUpdated) {
    updateGreeting(username);
    isGreetingUpdated = true;  // Prevent further updates
  }
}

// Update time every second
setInterval(updateTime, 1000);

// Call this function once on page load to update the greeting
fetchUsernameAndUpdateGreeting();
