require(['jquery'], function slideComponent($) {
  function getFormVariables(event, form = null) {
    form = form || document.getElementById('edit_tile') || document.getElementById('add_tile');
    if (!form) {
      return;
    }
    try {
      form.querySelector('.formControls').setAttribute('style', 'display: none;');
    } catch (e) {}
    const typeAndTextFieldset = document.getElementById('fieldset-type_and_text');
    const positioningFieldset = document.getElementById('fieldset-text_positioning');
    const mediaFieldset = document.getElementById('fieldset-media_settings');
    const relatedItemsFieldset = document.getElementById('fieldset-related_items');
    const formVariables = {
      form,
      typeAndTextFieldset,
      positioningFieldset,
      mediaFieldset,
      relatedItemsFieldset,
      formFields: [
        ...Array.from(typeAndTextFieldset.children).filter(hasId),
        ...Array.from(positioningFieldset.children).filter(hasId),
        ...Array.from(mediaFieldset.children).filter(hasId),
        ...Array.from(relatedItemsFieldset.children).filter(hasId),
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

  function hasId(element) {
    return !!element.id;
  }

  function getItemsToHide(slideType) {
    const showAndHide = {};
    const imageSlidetypes = ['background-image', 'left-image-right-text'];
    const videoSlidetypes = ['background-video', 'left-video-right-text'];
    const backgroundSlidetypes = ['background-image', 'background-video'];
    const sideSlideTypes = ['left-image-right-text', 'left-video-right-text'];
    const mediaSlidetypes = [...imageSlidetypes, ...videoSlidetypes];
    const fieldsetLabels = ['Type & Text', 'Text Positioning', 'Media Settings', 'Related Items'];
    if (imageSlidetypes.includes(slideType)) {
      showAndHide.fieldIdEndingsToHide = ['widgets-video', 'related_items'];
    }
    if (videoSlidetypes.includes(slideType)) {
      showAndHide.fieldIdEndingsToHide = ['widgets-image', 'related_items'];
    }
    if (slideType === 'resource-slide') {
      showAndHide.fieldIdEndingsToHide = [
        'widgets-image',
        'widgets-video',
        'widgets-title',
        'widgets-text',
        'hor_text_position',
        'vert_text_position',
      ];
    }
    if (mediaSlidetypes.includes(slideType)) {
      const hideLabels = ['Related Items'];
      showAndHide.hideFieldsetsWithLabels = hideLabels;
      showAndHide.unhideFieldsetsWithLabels = fieldsetLabels.filter((label) => !hideLabels.includes(label));
    } else {
      const hideLabels = ['Text Positioning', 'Mobile Text Positioning', 'Media Settings'];
      showAndHide.hideFieldsetsWithLabels = hideLabels;
      showAndHide.unhideFieldsetsWithLabels = fieldsetLabels.filter((label) => !hideLabels.includes(label));
    }
    if (backgroundSlidetypes.includes(slideType)) {
      showAndHide.fieldIdEndingsToHide.push('widgets-customize_left_slide_mobile');
      showAndHide.hideFieldsetsWithLabels.push('Mobile Text Positioning');
    }
    return showAndHide;
  }

  function shouldFieldBeDisplayed(id, idEndingsToHide) {
    return !idEndingsToHide.some((ending) => id.endsWith(ending));
  }

  function showAndHideFieldsAndFieldsets(form) {
    const { slideType, formFields } = form;
    const { fieldIdEndingsToHide, hideFieldsetsWithLabels, unhideFieldsetsWithLabels } = getItemsToHide(slideType);
    _showAndHideFields(formFields, fieldIdEndingsToHide);
    _showAndHideFieldsets(hideFieldsetsWithLabels, unhideFieldsetsWithLabels);
  }

  function _showAndHideFields(formFields, fieldIdEndingsToHide) {
    formFields.forEach((formField) => {
      const id = formField.id;
      if (shouldFieldBeDisplayed(id, fieldIdEndingsToHide)) {
        formField.removeAttribute('style');
      } else {
        formField.setAttribute('style', 'display: none;');
      }
    });
  }

  function _showAndHideFieldsets(hideFieldsetsWithLabels, unhideFieldsetsWithLabels) {
    potentialFormTabs = Array.from(document.querySelectorAll('nav>a'));
    potentialFormTabs.forEach((tab) => {
      if (hideFieldsetsWithLabels.includes(tab.textContent)) {
        tab.setAttribute('style', 'display: none;');
      } else if (unhideFieldsetsWithLabels.includes(tab.textContent)) {
        tab.removeAttribute('style');
      }
    });
  }

  function _showAndHideSpecificFieldset(fieldsetText, show) {
    potentialFormTabs = Array.from(document.querySelectorAll('nav>a'));
    potentialFormTabs.some((tab) => {
      if (tab.textContent === fieldsetText) {
        if (show) {
          tab.removeAttribute('style');
        } else {
          tab.setAttribute('style', 'display: none;');
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
            showAndHideFieldsAndFieldsets(formVariables);
            $('#form-widgets-display_type').change(onSlideTypeChange);
            toggleMobileTextPositionFieldset();
            $('#form-widgets-customize_left_slide_mobile-0').change(toggleMobileTextPositionFieldset);
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
    const observerOptions = {
      childList: true,
      attributes: false,
      subtree: true,
    };
    observer.observe(body, observerOptions);
  }

  function onSlideTypeChange(event) {
    const form = getFormVariables(event);
    showAndHideFieldsAndFieldsets(form);
  }

  function toggleMobileTextPositionFieldset() {
    const showMobile = $('#form-widgets-customize_left_slide_mobile-0')[0].checked;
    _showAndHideSpecificFieldset('Mobile Text Positioning', showMobile);
  }

  if (!window.slideScriptCalled) {
    window.slideScriptCalled = true;
    $('document').ready(observe);
  }
  toggleMobileTextPositionFieldset;
});
