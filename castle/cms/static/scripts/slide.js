function getVariables(event) {
    const slideType = event.target.value;
    const form = event.target.closest('form');
    const formElements = Array.from(form.children).filter(element=>!!element.id);
    return {slideType, form, formElements};
}
function shouldElementBeHidden(id, idEndingsToHide) {
    return idEndingsToHide.some(ending => id.endsWith(ending));
}
function hideFields(formElements, slideType) {
    const idEndingsToHide = getIdEndingsToHide(slideType);
    console.log(`slide type: ${slideType}, endingsToHide: ${idEndingsToHide}`);
    formElements.forEach(formElement => {
        const id = formElement.id;
        if (shouldElementBeHidden(id, idEndingsToHide)) {
            formElement.hidden = true;
        } else {
            formElement.hidden = false;
        }
    });
}
function getIdEndingsToHide(slideType) {
    switch (slideType) {
        case 'background-image':
        case 'left-image-right-text':
            return ['slide-video'];
        case 'background-video':
        case 'left-video-right-text':
            return ['slide-image'];
        case 'resource-slide':
            return ['slide-image', 'slide-video'];
        default:
            return [];
    }
}
function onSlideTypeChange(event) {
    console.log(event);
    const {slideType, form, formElements} = getVariables(event);
    console.log(formElements);
    hideFields(formElements, slideType);
}
function modifyEditTile(mutations) {
    const editTile = document.getElementById('edit_tile');
    if (editTile) {
        const formElements = Array.from(editTile.children).filter((element) => !!element.id);
        const slideTypeSelect = editTile.querySelector("select[id$='slide-display_type'");
        const slideType = slideTypeSelect.options[slideTypeSelect.selectedIndex].value;
        console.log(slideType);
        hideFields(formElements, slideType);     
    }
}
function observe() {
    const observer = new MutationObserver(modifyEditTile);
    const body = document.querySelector('body');
    const observerOptions = { childList: true, attributes: false, subtree: true };
    observer.observe(body, observerOptions);
}



// castle attempts to execute this script multiple times, so block the rest
if (!window.scriptCalled) {
    window.scriptCalled = true;
    observe();
}