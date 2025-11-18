$(document).ready(function () {
    const toggleSwitch = $('#dark-mode-toggle');

    // Check if dark mode is enabled in localStorage and set it initially
    if (localStorage.getItem('darkMode') === 'enabled') {
        enableDarkMode();
    } else {
        disableDarkMode();
    }

    // Toggle dark mode on button click
    toggleSwitch.on('click', function () {
        if (localStorage.getItem('darkMode') !== 'enabled') {
            enableDarkMode();
        } else {
            disableDarkMode();
        }
    });

    // Function to enable dark mode
    function enableDarkMode() {
        $('body').addClass('dark-mode');
        toggleSwitch.text('Disable Dark Mode');
        localStorage.setItem('darkMode', 'enabled');
    }

    // Function to disable dark mode
    function disableDarkMode() {
        $('body').removeClass('dark-mode');
        toggleSwitch.text('Enable Dark Mode');
        localStorage.setItem('darkMode', 'disabled');
    }
});