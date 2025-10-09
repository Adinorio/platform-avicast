"""
Browser Diagnostic Script
Run this in your browser console (F12) to diagnose the issue
"""

console.log("=== AVICAST ANALYTICS DIAGNOSTIC ===");

// Check current URL
console.log("Current URL:", window.location.href);

// Check if we're on the right page
if (window.location.pathname.includes('/analytics/')) {
    console.log("✅ On analytics page");
} else {
    console.log("❌ NOT on analytics page - current path:", window.location.pathname);
}

// Check for raw template tags
const bodyText = document.body.innerText;
if (bodyText.includes('{% include')) {
    console.log("❌ PROBLEM: Raw {% include %} tags found in page!");
    console.log("First occurrence:", bodyText.match(/{% include[^}]+%}/)[0]);
} else {
    console.log("✅ SUCCESS: No raw template tags found");
}

// Check for success banner
if (bodyText.includes('Success! Analytics dashboard rendered correctly')) {
    console.log("✅ SUCCESS: Success banner found");
} else {
    console.log("❌ PROBLEM: Success banner not found");
}

// Check for metric cards
if (document.querySelector('.metric-card')) {
    console.log("✅ SUCCESS: Metric cards found");
} else {
    console.log("❌ PROBLEM: No metric cards found");
}

// Check page title
console.log("Page title:", document.title);

// Check for JavaScript errors
console.log("=== CHECK CONSOLE FOR ERRORS ABOVE ===");

// Test network request
fetch('/analytics/')
    .then(response => {
        console.log("Network request status:", response.status);
        console.log("Content-Type:", response.headers.get('Content-Type'));
        return response.text();
    })
    .then(html => {
        console.log("Response length:", html.length, "characters");
        if (html.includes('{% include')) {
            console.log("❌ SERVER PROBLEM: Server is sending raw template code!");
        } else {
            console.log("✅ SERVER OK: Server sending proper HTML");
        }
    })
    .catch(error => {
        console.log("❌ Network error:", error);
    });

console.log("=== DIAGNOSTIC COMPLETE ===");
