const backLink = document.querySelector('[data-back-link]');

// Keep the home URL as a safe fallback when there is no previous local page.
if (backLink && document.referrer) {
    const previousPage = new URL(document.referrer);

    // Never send the visitor back to an external site from this control.
    if (previousPage.origin === window.location.origin) {
        backLink.addEventListener('click', (event) => {
            event.preventDefault();
            window.history.back();
        });
    }
}
