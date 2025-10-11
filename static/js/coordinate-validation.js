/**
 * Real-time coordinate validation and formatting
 * Provides client-side validation for coordinate input fields
 */

document.addEventListener('DOMContentLoaded', function() {
    const coordinateInputs = document.querySelectorAll('.coordinate-input');
    
    coordinateInputs.forEach(function(input) {
        // Add real-time validation
        input.addEventListener('input', function() {
            validateCoordinateInput(this);
        });
        
        // Add blur event for final validation
        input.addEventListener('blur', function() {
            formatCoordinateInput(this);
        });
        
        // Add help text for coordinate formats
        addCoordinateHelpText(input);
    });
});

function validateCoordinateInput(input) {
    const value = input.value.trim();
    const feedback = getOrCreateFeedback(input);
    
    if (!value) {
        clearValidation(input, feedback);
        return;
    }
    
    try {
        // Test if the coordinate can be parsed
        const normalized = parseCoordinateInput(value);
        showValidationSuccess(input, feedback, `Valid: ${normalized}`);
    } catch (error) {
        showValidationError(input, feedback, error.message);
    }
}

function formatCoordinateInput(input) {
    const value = input.value.trim();
    if (!value) return;
    
    try {
        const normalized = parseCoordinateInput(value);
        input.value = normalized;
        showValidationSuccess(input, getOrCreateFeedback(input), 'Coordinates normalized');
    } catch (error) {
        // Keep original value if parsing fails
        console.warn('Coordinate parsing failed:', error.message);
    }
}

function parseCoordinateInput(input) {
    /**
     * Client-side coordinate parsing (matches server-side logic)
     */
    if (!input || !input.trim()) {
        throw new Error('Coordinates cannot be empty');
    }
    
    const inputStr = input.trim();
    
    // Handle degree-minute-second format (basic)
    if (/[°'"']/.test(inputStr)) {
        return parseDMSFormat(inputStr);
    }
    
    // Handle decimal formats
    return parseDecimalFormat(inputStr);
}

function parseDecimalFormat(inputStr) {
    // Split by common delimiters
    for (const delimiter of [',', ';', '|']) {
        if (inputStr.includes(delimiter)) {
            const parts = inputStr.split(delimiter);
            if (parts.length >= 2) {
                const lat = parseFloat(parts[0].trim());
                const lon = parseFloat(parts[1].trim());
                return normalizeCoordinates(lat, lon);
            }
        }
    }
    
    // Try space-separated
    const parts = inputStr.split(/\s+/);
    if (parts.length >= 2) {
        const lat = parseFloat(parts[0].trim());
        const lon = parseFloat(parts[1].trim());
        return normalizeCoordinates(lat, lon);
    }
    
    throw new Error(`Invalid coordinate format: ${inputStr}`);
}

function parseDMSFormat(inputStr) {
    // Basic DMS regex pattern
    const dmsPattern = /(\d+)°(\d+)'([\d.]+)"([NS])\s*,\s*(\d+)°(\d+)'([\d.]+)"([EW])/;
    const match = inputStr.match(dmsPattern);
    
    if (!match) {
        throw new Error(`Invalid DMS format: ${inputStr}`);
    }
    
    const [, latDeg, latMin, latSec, latDir, lonDeg, lonMin, lonSec, lonDir] = match;
    
    let lat = parseFloat(latDeg) + parseFloat(latMin) / 60 + parseFloat(latSec) / 3600;
    let lon = parseFloat(lonDeg) + parseFloat(lonMin) / 60 + parseFloat(lonSec) / 3600;
    
    if (latDir === 'S') lat = -lat;
    if (lonDir === 'W') lon = -lon;
    
    return normalizeCoordinates(lat, lon);
}

function normalizeCoordinates(lat, lon) {
    // Validate latitude (-90 to 90)
    if (isNaN(lat) || lat < -90 || lat > 90) {
        throw new Error(`Latitude must be between -90 and 90, got ${lat}`);
    }
    
    // Validate longitude (-180 to 180)
    if (isNaN(lon) || lon < -180 || lon > 180) {
        throw new Error(`Longitude must be between -180 and 180, got ${lon}`);
    }
    
    // Round to 6 decimal places
    lat = Math.round(lat * 1000000) / 1000000;
    lon = Math.round(lon * 1000000) / 1000000;
    
    return `${lat}, ${lon}`;
}

function getOrCreateFeedback(input) {
    let feedback = input.parentNode.querySelector('.coordinate-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'coordinate-feedback form-text';
        input.parentNode.appendChild(feedback);
    }
    return feedback;
}

function showValidationSuccess(input, feedback, message) {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    feedback.className = 'coordinate-feedback form-text text-success';
    feedback.textContent = message;
}

function showValidationError(input, feedback, message) {
    input.classList.remove('is-valid');
    input.classList.add('is-invalid');
    feedback.className = 'coordinate-feedback form-text text-danger';
    feedback.textContent = message;
}

function clearValidation(input, feedback) {
    input.classList.remove('is-valid', 'is-invalid');
    feedback.className = 'coordinate-feedback form-text';
    feedback.textContent = '';
}

function addCoordinateHelpText(input) {
    const helpText = document.createElement('small');
    helpText.className = 'form-text text-muted coordinate-help';
    helpText.innerHTML = `
        <strong>Accepted formats:</strong><br>
        • Decimal: <code>14.5995, 120.9842</code><br>
        • DMS: <code>14°35'58.2"N, 120°59'3.1"E</code><br>
        • Separators: comma (,), semicolon (;), pipe (|), or space
    `;
    input.parentNode.appendChild(helpText);
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        parseCoordinateInput,
        parseDecimalFormat,
        parseDMSFormat,
        normalizeCoordinates
    };
}
