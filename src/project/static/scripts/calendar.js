let currentDate = new Date();
let currentMonth = currentDate.getMonth() + 1; // getMonth() is zero-based
let currentYear = currentDate.getFullYear();
let currentButton = null;

const monthNamesRussian = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
];

function fetchCalendarData(month, year) {
    return fetch(`/calendar/${month}/${year}`)
        .then((response) => response.json())
        .catch((error) => console.error(error));
}

function fetchEventData(month, year) {
    return fetch(`/events/${month}/${year}`)
        .then((response) => response.json())
        .catch((error) => console.error(error));
}

function renderEvents(events) {
    const eventsContainer = document.querySelector("#events");
    eventsContainer.innerHTML = ""; // Clear the events container

    events.forEach((event) => {
        const li = document.createElement("li");
        li.className = `rounded-lg shadow-[rgba(0,_0,_0,_0.24)_0px_3px_8px] py-5 w-full px-2 flex flex-col border-l-8 border-${event.event_color}`;
        li.dataset.datetime = event.date;

        const eventName = document.createElement("span");
        eventName.className = "font-semibold";
        eventName.textContent = event.name + " ";

        const eventDateString = document.createElement("span");
        eventDateString.className = "font-normal text-sm text-gray-400";
        eventDateString.textContent = event.date_string;
        eventName.appendChild(eventDateString);

        const eventDescription = document.createElement("span");
        eventDescription.className = "text-sm text-gray-600";
        eventDescription.textContent = event.description;

        li.appendChild(eventName);
        li.appendChild(eventDescription);

        eventsContainer.appendChild(li);
    });
}

function renderCalendar(data) {
    const calendarContainer = document.querySelector("#month-matrix");
    calendarContainer.innerHTML = "";
    data.matrix.forEach((week) => renderWeek(week, data, calendarContainer));
}

function renderWeek(week, data, calendarContainer) {
    const weekDiv = document.createElement("div");
    weekDiv.className = "flex";
    week.forEach((day) => renderDay(day, data, weekDiv));
    calendarContainer.appendChild(weekDiv);
}

function renderDay(day, data, weekDiv) {
    const button = document.createElement("button");
    const event_indicators = document.createElement("div");
    event_indicators.className = "flex flex-row justify-center items-center gap-1";
    button.type = "button";
    button.id = `${data.year}-${data.month}-${day.day}`;
    button.className =
        "sm:m-2 m-px sm:size-12 size-10 flex flex-col justify-center items-center border border-transparent sm:text-xl text-sm text-gray-800 hover:bg-gray-200 rounded-xl";
    button.onclick = function () {
        handleDayClick(this);
    };
    if (day.day === "") {
        button.className += " pointer-events-none";
    }

    day.events.forEach((event) => {
        const event_indicator = document.createElement("div");
        event_indicator.className = "size-1 sm:size-2 rounded-full";
        event_indicator.classList.add(`bg-${event}`);
        event_indicators.appendChild(event_indicator);
    });
    button.textContent = day.day;
    button.appendChild(event_indicators);
    weekDiv.appendChild(button);
}

function handleDayClick(button) {
    // If the clicked button is the currently selected button, deselect it and hide all events
    if (button === currentButton) {
        button.classList.remove("bg-sky-400", "hover:bg-sky-300", "text-white");
        button.classList.add("hover:bg-gray-200");
        currentButton = null;
        showDayEvents(""); // Hide all events
        return;
    }

    showDayEvents(button.id);
    if (currentButton) {
        currentButton.classList.remove("bg-sky-400", "hover:bg-sky-300", "text-white");
        currentButton.classList.add("hover:bg-gray-200");
    }
    button.classList.add("bg-sky-400", "hover:bg-sky-300", "text-white");
    button.classList.remove("hover:bg-gray-200");
    currentButton = button;
}

function setMonthName() {
    document.querySelector("#month-name").textContent = monthNamesRussian[currentMonth - 1];
}

function prevMonth() {
    if (--currentMonth < 1) {
        currentMonth = 12;
        currentYear--;
    }
    fetchCalendarData(currentMonth, currentYear).then(renderCalendar);
    fetchEventData(currentMonth, currentYear).then(renderEvents);
    setMonthName();
    showDayEvents(""); // Hide all events
}

function nextMonth() {
    if (++currentMonth > 12) {
        currentMonth = 1;
        currentYear++;
    }
    fetchCalendarData(currentMonth, currentYear).then(renderCalendar);
    fetchEventData(currentMonth, currentYear).then(renderEvents);
    setMonthName();
    showDayEvents(""); // Hide all events
}

function showDayEvents(date) {
    if (!date) {
        // Hide all events
        const allEvents = document.querySelectorAll("#events li");
        allEvents.forEach((event) => event.classList.remove("hidden"));
        return;
    }

    let [year, month, day] = date.split("-");
    month = month.padStart(2, "0");
    day = day.padStart(2, "0");
    const formattedDate = `${year}-${month}-${day}`;

    // Hide all events
    const allEvents = document.querySelectorAll("#events li");
    allEvents.forEach((event) => event.classList.add("hidden"));

    // Show only the events that match the selected date
    const matchingEvents = document.querySelectorAll(`#events li[data-datetime="${formattedDate}"]`);
    matchingEvents.forEach((event) => event.classList.remove("hidden"));
}

fetchCalendarData(currentMonth, currentYear).then(renderCalendar);
fetchEventData(currentMonth, currentYear).then(renderEvents);
setMonthName();
