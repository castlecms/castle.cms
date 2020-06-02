function getFormVariables(event) {
    const form = document.getElementById('edit_tile');
    if (!form) {
        return;
    }
    const typeAndTextFieldset = document.getElementById('fieldset-type-and-text');
    const mediaFieldset = document.getElementById('fieldset-media-settings');
    const formVariables = {
        form,
        typeAndTextFieldset,
        mediaFieldset,
        formFields: [
            ...Array.from(typeAndTextFieldset.children).filter(hasId),
            ...Array.from(mediaFieldset.children).filter(hasId)
        ],
        navTabs: form.querySelector('nav')
    };
    if (event) {
        formVariables.slideType = event.target.value;
    } else {
        const slideTypeSelect = form.querySelector("select[id$='widgets-display_type'");
        formVariables.slideType = slideTypeSelect.options[slideTypeSelect.selectedIndex].value;
    }
    return formVariables;
}
function shouldElementBeHidden(id, idEndingsToHide) {
    return idEndingsToHide.some(ending => id.endsWith(ending));
}
function hideFields(form) {
    const { slideType, formFields } = form;
    const idEndingsToHide = getIdEndingsToHide(slideType);
    formFields.forEach((formField) => {
      const id = formField.id;
      if (shouldElementBeHidden(id, idEndingsToHide)) {
        formField.hidden = true;
      } else {
        formField.hidden = false;
      }
    });
}
function getIdEndingsToHide(slideType) {
    switch (slideType) {
        case 'background-image':
        case 'left-image-right-text':
            return ['widgets-video', 'related_items'];
        case 'background-video':
        case 'left-video-right-text':
            return ['widgets-image', 'related_items'];
        case 'resource-slide':
            return ['widgets-image', 'widgets-video'];
        default:
            return [];
    }
}
function onSlideTypeChange(event) {
    const form = getFormVariables(event);
    hideFields(form);
}
function hasId(element) {
    return !!element.id;
}
function modifyEditTile(mutations) {
    const form = getFormVariables();
    if (form) {
        hideFields(form);
        // updateFieldsets(form);
    }
}
function observe() {
    const observer = new MutationObserver(modifyEditTile);
    const body = document.querySelector('body');
    const observerOptions = { childList: true, attributes: false, subtree: true };
    observer.observe(body, observerOptions);
}



// castle attempts to execute this script multiple times, so block the rest
if (!window.slideScriptCalled) {
    window.slideScriptCalled = true;
    observe();
}