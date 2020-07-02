function getFormVariables(event) {
    const form = document.getElementById('edit_tile') ||
        document.getElementById('add_tile');
    if (!form) {
        return;
    }
    try {
        form.querySelector('.formControls').setAttribute('style', 'display: none;');
    } catch (e) {}
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
        navTabs: Array.from(form.querySelector('nav').children)
    };
    if (event) {
        formVariables.slideType = event.target.value;
    } else {
        const slideTypeSelect = form.querySelector("select[id$='widgets-display_type'");
        formVariables.slideType = slideTypeSelect.options[slideTypeSelect.selectedIndex].value;
    }
    return formVariables;
}
function shouldElementBeDisplayed(id, idEndingsToHide) {
    return !idEndingsToHide.some(ending => id.endsWith(ending));
}
function hideFields(form) {
    const { slideType, formFields } = form;
    const idEndingsToHide = getIdEndingsToHide(slideType);
    formFields.forEach((formField) => {
      const id = formField.id;
      if (shouldElementBeDisplayed(id, idEndingsToHide)) {
        formField.removeAttribute('style');
    } else {
        formField.setAttribute('style', 'display: none;');
      }
    });
    potentialFormTabs = Array.from(document.querySelectorAll('nav>a'));
    potentialFormTabs.some(tab => {
        if (tab.textContent === 'Media Settings') {
            if (slideType === 'resource-slide') {
                tab.setAttribute('style', 'display: none;');
            } else {
                tab.removeAttribute('style');
            }
            return true;
        }
        return false;
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
            return ['widgets-image', 'widgets-video', 'widgets-title',
                    'widgets-text', 'hor_text_position', 'vert_text_position'];
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
function modifyAddEditTile(mutations) {
    const form = getFormVariables();
    if (form) {
        hideFields(form);
    }
}
async function observe() {
    const observer = new MutationObserver(modifyAddEditTile);
    const body = await getBody();
    const observerOptions = { childList: true, attributes: false, subtree: true };
    observer.observe(body, observerOptions);
}
function getBody() {
    return new Promise((resolve, reject) => {
        let counter = 0;
        interval = setInterval(() => {
            counter++;
            const body = document.querySelector('body');
            if (body) {
                clearInterval(interval);
                resolve(body);
            }
            if (counter > 30) {
                reject('Could not find body element after 30 seconds');
            }
        }, 1000)
    });
}


// castle attempts to execute this script multiple times, so block the rest
if (!window.slideScriptCalled) {
    window.slideScriptCalled = true;
    observe();
}