var calendar;

document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        events: '/calendar',
        eventContent: function(arg) {
            // Custom content for events
            var titleEl = document.createElement('div');
            titleEl.innerText = arg.event.title;
            var timeEl = document.createElement('div');
            timeEl.innerText = arg.event.start.toLocaleTimeString();
            return { domNodes: [titleEl, timeEl] };
        },
        eventDidMount: function(arg) {
            // Custom styles for events
            var color = getEventColor(arg.event.extendedProps.machine_type);
            arg.el.style.backgroundColor = color;
        }
    });
    calendar.render();
});

function getEventColor(machineType) {
    switch (machineType) {
        case 'TB1': return '#FF6347';
        case 'TB2': return '#4682B4';
        case 'VB1': return '#32CD32';
        case 'VB2': return '#FFD700';
        case 'U':   return '#D2691E';
        default:    return 'gray';
    }
}

function filterEvents(machineType) {
    fetch('/calendar')
    .then(response => response.json())
    .then(data => {
        var filteredEvents = data.filter(event => machineType === 'all' || event.machine_type === machineType);
        calendar.removeAllEvents();
        calendar.addEventSource(filteredEvents);
    });
}