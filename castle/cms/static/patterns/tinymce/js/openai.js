/**
 * plugin.js
 *
 * Released under LGPL License.
 * Copyright (c) 1999-2015 Ephox Corp. All rights reserved
 *
 * License: http://www.tinymce.com/license
 * Contributing: http://www.tinymce.com/contributing
 */

/*global tinymce:true */
define(['jquery', 'tinymce'], function($, tinymce) {
	// $.mosaic.actionManager.actions
	tinymce.PluginManager.add('openai', function (editor) {
		'use strict';
		function showDialog() {
			editor.windowManager.open({
				title: 'AI Assistant',
				body: [
					{
						type: 'textbox', 
						name: 'request',
						placeholder: 'Ask the AI to edit or generate...',
					},
				],
				height: 60,
				width: 600,
				onsubmit: async function(e) {
					const { portalUrl } = document.querySelector( 'body' ).dataset;
					
					function dimScreen() {
						let element = document.querySelector('#dimmer')
						if (element === null){
							const dimmer = document.createElement('div');
							dimmer.id = 'dimmer'
							dimmer.style.display = 'block'
							dimmer.style.backgroundColor = 'black'
							dimmer.style.position = 'fixed';
							dimmer.style.width = '100%';
							dimmer.style.height = '100%';
							dimmer.style.zIndex = 1000;
							dimmer.style.top = '0px';
							dimmer.style.left = '0px';
							dimmer.style.opacity = .5; /* in FireFox */ 
							document.body.appendChild(dimmer)
						}
						else {
							element.style.display = 'block'
						}
					}

					function hideDimmer() {
						const element = document.querySelector('#dimmer')
						element.style.display = 'none'
					}

					function showSpinner() {
						dimScreen()
						let element = document.querySelector('#spinner')
						if (element === null){
							const spinnerImg = document.createElement('img');
							spinnerImg.src = '++plone++castle/svg/tinymce/spinner-solid.svg'
							spinnerImg.id = 'spinner'
							spinnerImg.classList = 'text-center'
							spinnerImg.style.position = 'fixed';
							spinnerImg.style.top = '50%';
							spinnerImg.style.left = '50%';
							spinnerImg.style.height = '100px';
							spinnerImg.style.width = '100px';
							spinnerImg.style.transform = 'translate(-50%, -50%)';
							spinnerImg.style.zIndex = '70000'
							spinnerImg.style.display = 'block'
							document.body.appendChild(spinnerImg)
							spin()
						}
						else {
							element.style.display = 'block'
						}
					}

					function hideSpinner() {
						const spinnerElm = document.querySelector('#spinner')
						spinnerElm.style.display = 'none'
						hideDimmer()
					}

					function spin() {
						const loadingSpinning = [
							{ transform: 'rotate(0)' },
							{ transform: 'rotate(360deg)' },
						];
							
						const loadingTiming = {
							duration: 2000,
							iterations: Infinity,
						};
							
						const loading = document.querySelector('#spinner');
						loading.animate(loadingSpinning, loadingTiming);
					}	
					
					function delay(time) {
						return new Promise(resolve => setTimeout(resolve, time));
					}

					function checkFormExists() {
						if (document.querySelector('#openai-form') == null) {
							const form = document.createElement('form');
							form.id = 'openai-form'
							const requestInput = document.createElement('input');
							form.method = 'POST';

							requestInput.name='data';
							requestInput.id='openai-request-input'
							form.appendChild(requestInput);  
							
							form.style.display = 'none'
							document.body.appendChild(form);
						}
					}

					async function openAiRequest() {
						checkFormExists()
						const input = document.querySelector('#openai-request-input')
						input.value = e.data.request
						const form = document.querySelector('#openai-form')
						
						const request = await fetch(`${portalUrl}/@@openai-request`, {
							method: 'POST',
							body: new URLSearchParams(new FormData(form))
						}).then(async response => {
							const jsonResponse = await response.json()
							if (!response.ok) {
								if (response.status === 401) {
									hideSpinner()
									await delay(100);
									alert('Invalid authentication or api key. Please contact your administrator.')
									
								}
								else if (response.status === 429) {
									if (jsonResponse.error.type === 'insufficient_quota') {
										hideSpinner()
										await delay(100);
										alert('You used up your monthly requests. Please message your administrator to load more.')
									}
									else {
										hideSpinner()
										await delay(100);
										alert('Too many requests have been submited to OpenAI. Please try again later.')
									}
								}
								else if (response.status >= 500) {
									hideSpinner()
									await delay(100);
									alert('There has been an error connecting to OpenAI. Please try again later.')
								}
								else {
									hideSpinner()
									await delay(100);
									alert('There has been an unexpected error. Please contact your administrator.')
								}
							}
							else {
								hideSpinner()
								return await jsonResponse;
							}						
						})
						.catch(async (error) => {
							hideSpinner()
							await delay(100);
							alert('There has been an unexpected error. Please contact your administrator.')
						});
						return request
					}

					showSpinner()
					const requestJson = openAiRequest()
					const answer = await requestJson
					editor.insertContent(answer.message);
				}
			});
		}

		editor.addButton('openai', {
			icon: 'openai',
			tooltip: 'OpenAI',
			onclick: showDialog,
		});
	});
})
