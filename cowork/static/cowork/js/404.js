const backLink = document.querySelector('[data-back-link]');

if (backLink && document.referrer) {
    const previousPage = new URL(document.referrer);

    if (previousPage.origin === window.location.origin) {
        backLink.addEventListener('click', (event) => {
            event.preventDefault();
            window.history.back();
        });
    }
}
