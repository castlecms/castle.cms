var FakeGrunt = function(){
  this.config = {};
  this.deferredLoad = [];
  this.deferredTasks = {};
  this.file = {
    readJSON: function(){}
  };
};
FakeGrunt.prototype.initConfig = function(config){
  this.config = config;
};
FakeGrunt.prototype.loadNpmTasks = function(tasks){
  this.deferredLoad.push(tasks);
};
FakeGrunt.prototype.registerTask = function(name, tasks){
  this.deferredTasks[name] = tasks;
};

var originalGruntFile = require('./Gruntfile.js');

Array.prototype.removeElement = function(value) {
  var index = this.indexOf(value);
  if (index > -1) {
    this.splice(index, 1);
  }
};

module.exports = function (grunt) {
  'use strict';
  var fakeGrunt = new FakeGrunt();
  originalGruntFile(fakeGrunt);
  var config = fakeGrunt.config;

  delete config.pkg;

  var ploneTasks = fakeGrunt.deferredTasks['compile-plone'].slice();
  ploneTasks.removeElement('requirejs:plone');
  ploneTasks.removeElement('uglify:plone');
  var ploneLoggedInTasks = fakeGrunt.deferredTasks['compile-plone-logged-in'].slice();
  ploneLoggedInTasks.removeElement('requirejs:plone-logged-in');
  ploneLoggedInTasks.removeElement('uglify:plone-logged-in');

  config.watch = {
    'plone-less': {
      files: [
        '%(castle)s/less/*.less'
      ],
      tasks: ploneTasks
    },
    'plone-js': {
      files: [
        '%(castle)s/components/*.js',
        '%(castle)s/patterns/*.js',
      ],
      tasks: ['requirejs:plone']
    },
    'plone-logged-in-less': {
      files: [
        '%(castle)s/less/*.less'
      ],
      tasks: ploneLoggedInTasks
    },
    'plone-logged-in-js': {
      files: [
        '%(castle)s/components/*.js',
        '%(castle)s/patterns/*.js',
      ],
      tasks: ['requirejs:plone-logged-in']
    }
  };

  grunt.initConfig(config);

  var i;
  for(i=0; i<fakeGrunt.deferredLoad.length; i++){
    grunt.loadNpmTasks(fakeGrunt.deferredLoad[i]);
  }
  grunt.loadNpmTasks('grunt-contrib-watch');

  for(var taskName in fakeGrunt.deferredTasks){
    grunt.registerTask(taskName, fakeGrunt.deferredTasks[taskName]);
  }
  grunt.registerTask('watch-plone-less', ['watch:plone-less']);
  grunt.registerTask('watch-plone-logged-in-less', ['watch:plone-logged-in-less']);
  grunt.registerTask('watch-plone-js', ['watch:plone-js']);
  grunt.registerTask('watch-plone-logged-in-js', ['watch:plone-logged-in-js']);
  grunt.registerTask('less-plone', ploneTasks);
  grunt.registerTask('less-plone-logged-in', ploneLoggedInTasks);
  grunt.registerTask('js-plone', ['requirejs:plone']);
  grunt.registerTask('js-plone-logged-in', ['requirejs:plone-logged-in']);
  grunt.registerTask('js-plone-build', ['requirejs:plone', 'uglify:plone']);
  grunt.registerTask('js-plone-logged-in-build', ['requirejs:plone-logged-in', 'uglify:plone-logged-in']);

};
