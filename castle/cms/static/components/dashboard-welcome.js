require([
'jquery',
'castle-url/components/add-content-modal',
'castle-url/components/utils'
], function($, AddContentModal, cutils) {
'use strict';

$('.add-content-btn').on('click', function(e){
  e.preventDefault();
  var tbarSettings = cutils.getToolbarSettings();

  var selected = $(this).attr('data-type');
  var selectedType = null;
  tbarSettings.add.types.forEach(function(type){
    if(type.id === selected){
      selectedType = type;
    }
  });

  var component = cutils.createModalComponent(AddContentModal, 'add-modal-react-container', {
    types: tbarSettings.add.types
  });
  component.refs.tab.setState({
    selectedType: selectedType,
    basePath: $(this).attr('data-path')
  });
  component.forceUpdate();
});

$('.upload-content-btn').on('click', function(e){
  e.preventDefault();
  var component = cutils.createModalComponent(AddContentModal, 'add-modal-react-container', {});
  component.setState({
    selected: 'upload'
  })
});
});
