function updateFractionOptions() {
    var organType = document.getElementById('organ_type').value;
    var fractionSelect = document.getElementById('number_of_fractions');
    fractionSelect.innerHTML = '';

    var fractions = {
    'Craniospinal': [13, 17, 20, 30],
    'Breast': [15, 19, 25, 30],
    'Breast special': [15, 19, 25, 30],
    'Head & neck': [5, 10, 15, 25, 30, 33, 35],
    'Abdomen': [1, 3, 5, 8, 10, 12, 15, 18, 20, 30],
    'Pelvis': [1, 3, 5, 10, 15, 22, 23, 25, 28, 35],
    'Crane': [1, 5, 10, 13, 25, 30],
    'Lung': [1, 5, 10, 15, 20, 25, 30, 33],
    'Lung special': [3, 5, 8],
    'Whole Brain': [5, 10, 12]
    };

    var options = fractions[organType];
    options.forEach(function(fraction) {
        var option = document.createElement('option');
        option.value = fraction;
        option.text = fraction;
        fractionSelect.appendChild(option);
    });
}

// Call updateFractionOptions on page load to initialize the options
document.addEventListener('DOMContentLoaded', function() {
    updateFractionOptions();
});
