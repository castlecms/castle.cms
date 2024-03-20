function loadEmailTemplate( emailFormType /* 'subscribers' | 'users' */ ) {
  const button = document.querySelector( `button#load-email-template--${ emailFormType }` );
  const emailTemplateSelectForm = button.previousElementSibling;
  const subscriberEmailForm = button.nextElementSibling.nextElementSibling;
  const emailEditor = getEmailBodyRichTextEditor( subscriberEmailForm );
  if ( !emailEditor ) {
    return;
  }
  const emailTemplate = getEmailTemplate( emailTemplateSelectForm, emailFormType );
  if ( !emailTemplate || Object.keys( emailTemplate ).length === 0 ) {
    alert( 'Email Template not found' );
    return;
  }
  const {
    email_body: emailBody = null,
    email_subject: emailSubject = null,
    email_send_from: emailSendFrom = null,
    email_send_to_groups: emailSendToGroups = null,
    email_send_to_users: emailSendToUsers = null,
    email_send_to_subscriber_categories: emailSendToSubscriberCategories = null,
    email_send_to_custom: emailSendToCustom = null,
  } = emailTemplate;
  if ( emailBody ) {
    emailEditor.setContent( emailBody );
  }
  if ( emailSubject ) {
    const subjectField = document.querySelector( `.email-subject--${ emailFormType }` );
    if ( subjectField ) {
      subjectField.value = emailSubject;
    }
  }
  if ( emailSendFrom ) {
    const emailSendFromField = document.querySelector( `.email-send-from--${ emailFormType }` );
    if ( emailSendFromField ) {
      emailSendFromField.value = emailSendFrom;
    }
  }
  // some duplicate code - can likely be refactored
  if ( emailSendToSubscriberCategories ) {
    const sendToCategoriesField = subscriberEmailForm.querySelector( '#formfield-form-widgets-send_to_categories' );
    if ( sendToCategoriesField ) {
      const sendToCategoriesChildren = Array.from( sendToCategoriesField.children );
      const hiddenValueInput = sendToCategoriesChildren.filter(
        child => child.nodeName === 'INPUT' &&
          child.classList.contains( 'select2-offscreen' )
      )[ 0 ];
      if ( hiddenValueInput ) {
        hiddenValueInput.value = emailSendToSubscriberCategories.join( ';' );
      }
      const select2Div = sendToCategoriesChildren.filter(
        child => child.nodeName === 'DIV' &&
          child.classList.contains( 'select2-container' ) &&
          child.classList.contains( 'pat-select2' )
      )[ 0 ];
      const visibleSelectedCategoriesUl = select2Div.querySelector( 'ul' );
      const originalFirstLi = visibleSelectedCategoriesUl.firstChild;
      emailSendToSubscriberCategories
        .forEach(
          category => {
            const element = getLiChoiceElement( category, hiddenValueInput );
            visibleSelectedCategoriesUl.insertBefore( element, originalFirstLi );
          }
        );
    }
  }
  // some duplicate code - can likely be refactored
  if ( emailSendToUsers ) {
    const userIds = emailSendToUsers.map( user => user.user_id );
    // const userNames = emailSendToUsers.map( user => user.user_name );
    const sendToUsersField = subscriberEmailForm.querySelector( '#formfield-form-widgets-send_to_users' );
    if ( sendToUsersField ) {

      const sendToUsersChildren = Array.from( sendToUsersField.children );
      const hiddenValueInput = sendToUsersChildren.filter(
        child => child.nodeName === 'INPUT' &&
          child.classList.contains( 'select2-offscreen' )
      )[ 0 ];
      if ( hiddenValueInput ) {
        hiddenValueInput.value = userIds.join( ';' );
      }
      const select2Div = sendToUsersChildren.filter(
        child => child.nodeName === 'DIV' &&
          child.classList.contains( 'select2-container' ) &&
          child.classList.contains( 'pat-select2' )
      )[ 0 ];
      const visibleSelectedUsersUl = select2Div.querySelector( 'ul' );
      const originalFirstLi = visibleSelectedUsersUl.firstChild;
      emailSendToUsers
        .forEach(
          ( { user_id: userId, user_name: userName } ) => {
            const element = getLiChoiceElement( userName, hiddenValueInput, userId );
            visibleSelectedUsersUl.insertBefore( element, originalFirstLi );
          }
        );
    }
  }
  // some duplicate code - can likely be refactored
  if ( emailSendToGroups ) {
    const sendToGroupsField = subscriberEmailForm.querySelector( '#formfield-form-widgets-send_to_groups' );
    if ( sendToGroupsField ) {
      const sendToGroupsChildren = Array.from( sendToGroupsField.children );
      const hiddenValueInput = sendToGroupsChildren.filter(
        child => child.nodeName === 'INPUT' &&
          child.classList.contains( 'select2-offscreen' )
      )[ 0 ];
      if ( hiddenValueInput ) {
        hiddenValueInput.value = emailSendToGroups.join( ';' );
      }
      const select2Div = sendToGroupsChildren.filter(
        child => child.nodeName === 'DIV' &&
          child.classList.contains( 'select2-container' ) &&
          child.classList.contains( 'pat-select2' )
      )[ 0 ];
      const visibleSelectedGroupsUl = select2Div.querySelector( 'ul' );
      const originalFirstLi = visibleSelectedGroupsUl.firstChild;
      emailSendToGroups
        .forEach(
          groupName => {
            const element = getLiChoiceElement( groupName, hiddenValueInput );
            visibleSelectedGroupsUl.insertBefore( element, originalFirstLi );
          }
        );
    }
  }
  if ( emailSendToCustom ) {
    const sendToCustomField = subscriberEmailForm.querySelector( '#formfield-form-widgets-send_to_custom' );
    if ( sendToCustomField ) {
      const sendToCustomTextarea = Array.from( sendToCustomField.children )
        .filter( child => child.nodeName === 'TEXTAREA' )[ 0 ];
      if ( sendToCustomTextarea ) {
        sendToCustomTextarea.value = emailSendToCustom.join( '\n' );
        sendToCustomTextarea.rows = Math.min( emailSendToCustom.length, 15 );
        sendToCustomTextarea.scrollTop = sendToCustomTextarea.scrollHeight;
      }
    }
  }
};


function getLiChoiceElement( elementText, hiddenInput, hiddenValueToRemove = elementText ) {
  const li = document.createElement( 'li' );
  li.className = 'select2-search-choice';
  const div = document.createElement( 'div' );
  const divText = document.createTextNode( elementText );
  div.appendChild( divText );
  li.appendChild( div );
  const anchor = document.createElement( 'a' );
  anchor.href = '#';
  anchor.className = 'select2-search-choice-close';
  anchor.tabIndex = -1;
  // anchor.dataset.removeId = hiddenInputValueToRemove;
  anchor.onclick = getOnSelectedItemXClick( hiddenInput, hiddenValueToRemove );
  li.appendChild( anchor );
  return li;
}


function getOnSelectedItemXClick( hiddenInput, hiddenValueToRemove ) {
  return function onSelectedItemXClick( event ) {
    const { value: hiddenInputValue } = hiddenInput;
    hiddenInput.value = hiddenInputValue
      .split( ';' )
      .filter( value => value !== hiddenValueToRemove )
      .join( ';' );
    const { target: anchor } = event;
    const li = anchor.parentElement;
    if ( li.nodeName === 'LI' ) {
      li.remove();
    }
    // anchor.remove
  };
}


function getEmailBodyRichTextEditor( targetForm ) {
  const { editors: richTextEditors } = tinyMCE;
  return richTextEditors.reduce( ( accumulatedEditor, editor ) => {
    if ( accumulatedEditor === null ) {
      const editorForm = document.querySelector( `#${ editor.id }` ).closest( 'form' );
      if ( editorForm === targetForm ) { accumulatedEditor = editor; }
    }
    return accumulatedEditor;
  },
    null,
  );
}


function getEmailTemplate( targetForm, emailFormType ) {
  const emailTemplateValue = targetForm.querySelector( `.load-email-template-select--${ emailFormType }` )?.value;
  if ( !emailTemplateValue ) { return null; }
  try {
    return JSON.parse( emailTemplateValue );
  } catch ( e ) {
    return {};
  }
}
