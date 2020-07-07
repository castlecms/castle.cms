require(['jquery'], function myStuff($) {
  function getFormVariables(event, form = null) {
    form = form || document.getElementById('edit_tile') || document.getElementById('add_tile');
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
        ...Array.from(mediaFieldset.children).filter(hasId),
      ],
      navTabs: Array.from(form.querySelector('nav').children),
    };
    if (event) {
      formVariables.slideType = event.target.value;
    } else {
      const slideTypeSelect = form.querySelector("select[id$='widgets-display_type'");
      formVariables.slideType = slideTypeSelect.options[slideTypeSelect.selectedIndex].value;
    }
    return formVariables;
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
        return [
          'widgets-image',
          'widgets-video',
          'widgets-title',
          'widgets-text',
          'hor_text_position',
          'vert_text_position',
        ];
      default:
        return [];
    }
  }

  function hasId(element) {
    return !!element.id;
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
    potentialFormTabs.some((tab) => {
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

  function modifyAddEditTile(mutations) {
    mutations.some((mutation) => {
      const tileAdded = Array.from(mutation.addedNodes).some((addedNode) => {
        try {
          const form = addedNode.querySelector('#edit_tile') || addedNode.querySelector('#add_tile');
          if (form) {
            formVariables = getFormVariables(null, form);
            hideFields(formVariables);
            $('#form-widgets-display_type').change(onSlideTypeChange);
          }
          return !!form;
        } catch (err) {
          return false;
        }
      });
      return tileAdded;
    });
  }

  function observe() {
    const observer = new MutationObserver(modifyAddEditTile);
    const body = document.querySelector('body');
    const observerOptions = { childList: true, attributes: false, subtree: true };
    observer.observe(body, observerOptions);
  }

  function onSlideTypeChange(event) {
    const form = getFormVariables(event);
    hideFields(form);
  }

  function shouldElementBeDisplayed(id, idEndingsToHide) {
    return !idEndingsToHide.some((ending) => id.endsWith(ending));
  }

  if (!window.slideScriptCalled) {
    window.slideScriptCalled = true;
    $('document').ready(observe);
  }
});
