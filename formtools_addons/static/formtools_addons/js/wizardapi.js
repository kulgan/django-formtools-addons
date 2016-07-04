/**
 * Created by dirk on 17/05/16.
 */

(function() {
    var static_root = $('body').data('staticroot');
    var verbose = $('body').data('verbose') == '1';
    var wizard_template = $('body').data('template') || 'formtools_addons/templates/directives/wizardapi/wizard.html';
    var wizard_root = $('body').data('wizardroot') || '/wizard/';
    var substep_separator = '|';

    var getWizardUrl = function(path, endSlash){
        endSlash = endSlash || true;

        var result = wizard_root + path;
        if(endSlash && result.slice(-1) != '/'){
            result += '/';
        }

        return result;
    };

    var getWizardTemplate = function(){
        var templateUrl = static_root + wizard_template;
        if(verbose)console.log('getWizardTemplate', templateUrl);
        return templateUrl;
    };

    var parseStepName = function(stepName){
        /*
        Function to parse the current step (and substep if applicable)
         */
        var result = {
            fullStep: stepName
        };

        var splitItem = stepName.split(substep_separator);
        if(splitItem.length == 1){
            // Regular item
            result['step'] = splitItem;
            result['subStep'] = null;
        }
        else if(splitItem.length == 2){
            // SubStep item
            result['step'] = splitItem[0];
            result['subStep'] = splitItem[1];
        }
        return result;
    };

    var parseStepNames = function(stepNames){
        /*
        Function to parse WizardAPIView structure.
         */
        var getStepIndex = function(resultArray, step){
            var i = -1;
            var result = -1;
            resultArray.forEach(function(data){
                i += 1;
                if(data == step || data[0] == step){
                    result = i;
                }
            });
            return result;
        };

        var result = [];
        stepNames.forEach(function(stepName){
            var stepInfo = parseStepName(stepName);

            if(stepInfo.subStep == null){
                // Regular item (NOT TESTED)
                result.push(stepInfo.step);
            }
            else{
                // SubStep item
                var stepIndex = getStepIndex(result, stepInfo.step);
                if(stepIndex < 0){
                    result.push([stepInfo.step, []]);
                    stepIndex = getStepIndex(result, stepInfo.step);
                }
                var stepData = result[stepIndex];
                stepData[1].push(stepInfo.subStep);
            }
        });

        return result;
    };

    var transformSteps = function(steps){
        var stepNames = Object.keys(steps);

        var result = {};
        stepNames.forEach(function(stepName){
            var value = steps[stepName];

            var stepInfo = parseStepName(stepName);

            if(stepInfo.subStep == null){
                // Regular item (NOT TESTED)
                result[stepInfo.step] = value;
            }
            else{
                // SubStep item
                if(!result[stepInfo.step]){
                    result[stepInfo.step] = {};
                }
                result[stepInfo.step][stepInfo.subStep] = value;
            }
        });

        return result;
    };

    var transformData = function (data) {
        var fallback_step = data.structure[0];
        if (data.done) {
            fallback_step = data.structure[data.structure.length - 1];
        }

        var currentStepInfo = parseStepName(data.current_step || fallback_step);
        var structure = parseStepNames(data.structure);
        var steps = transformSteps(data.steps);

        data.structure = structure;
        data.current_step = currentStepInfo;
        data.steps = steps;

        return data;
    };

    $.fn.serializeObject = function(){
        var o = {};
        var a = this.serializeArray();
        $.each(a, function() {
            if (o[this.name] !== undefined) {
                if (!o[this.name].push) {
                    o[this.name] = [o[this.name]];
                }
                o[this.name].push(this.value || '');
            } else {
                o[this.name] = this.value || '';
            }
        });
        return o;
    };

    var app = angular.module('formtools_addons.WizardApp', ['ngCookies']);

    app.config(['$httpProvider', function($httpProvider){
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    }]);

    // http://stackoverflow.com/questions/17417607/angular-ng-bind-html-unsafe-and-directive-within-it
    app.directive('compile', ['$compile', function ($compile){
        return {
            link: function($scope, element, attrs){
                $scope.$watch(function($scope){
                    return $scope.$eval(attrs.compile);
                }, function(value){
                    element.html(value);
                    $compile(element.contents())($scope);
                });
            },
            scope: true
        };
    }]);

    app.directive('wizard', ['$http', function($http) {
        return {
            link: function($scope, elem, attrs){
                $scope.refresh = function(){
                    var promise = $http.get(getWizardUrl('data'));
                    promise.success(function(data){
                        $scope.handle_new_data(data);
                    }).error(function(){
                        $scope.error = true;
                    });
                };

                $scope.prev = function(){
                    var promise = $http.post(getWizardUrl('prev'));
                    promise.success(function(data){
                        $scope.handle_new_data(data);
                    }).error(function(){
                        $scope.error = true;
                    });

                    return false;
                };

                $scope.next = function(){
                    var promise = $http.post(getWizardUrl('next'));
                    promise.success(function(data){
                        $scope.handle_new_data(data);
                    }).error(function(){
                        $scope.error = true;
                    });

                    return false;
                };

                $scope.goto = function(step, substep){
                    var fullStep = step;
                    if(substep){
                        fullStep += substep_separator + substep;
                    }
                    var promise = $http.post(getWizardUrl('goto/' + fullStep));
                    promise.success(function(data){
                        $scope.handle_new_data(data);
                    }).error(function(){
                        $scope.error = true;
                    });

                    return false;
                };

                $scope.action_edit_step = function(subStep, step){
                    step = step || $scope.data.current_step.step;
                    $scope.goto(step, subStep);

                    return false;
                };

                $scope.action_submit_step = function(form_id){
                    var form = $('#' + form_id);
                    var form_data = form.serializeObject();
                    if(verbose)console.log(form_data);

                    var fullStepName = $scope.data.current_step.fullStep;

                    var promise = $http.post(getWizardUrl(fullStepName), form_data);
                    promise.success(function(data){
                        $scope.handle_new_data(data);
                    });
                    promise.error(function(data){
                        $scope.error = true;
                        $scope.handle_new_data(data);
                    });

                    return false;
                };

                $scope.action_step_back = function(){
                    var currentStepIndex = $scope.get_current_step_index();
                    if(currentStepIndex <= 0){
                        return;
                    }

                    var previousStep = $scope.get_step_by_index(currentStepIndex - 1);
                    var subSteps = $scope.get_sub_step_names(previousStep);
                    var subStep = subSteps[subSteps.length - 1];
                    $scope.refresh(previousStep, subStep);

                    return false;
                };

                $scope.handle_new_data = function(data){
                    data = transformData(data);
                    if(verbose)console.log(data);

                    if(data.done && data.valid){
                        $scope.handle_done(data);
                        return;
                    }

                    $scope.data = data;
                };

                $scope.handle_done = function(data){
                    var promise = $http.post(getWizardUrl('commit'));
                    promise.success(function(data){
                        if(verbose)console.log(data);
                        var next_url = data.next_url;
                        if(verbose)console.log('next_url:', next_url);
                        window.location = next_url;
                    });
                    promise.error(function(data){
                        $scope.error = true;
                        console.error(data);
                    });
                };

                $scope.get_step_by_index = function (index) {
                    var data = $scope.data.structure[index];
                    if(data instanceof Array){
                        return data[0];
                    }
                    else{
                        return data;
                    }
                };

                $scope.get_step_index = function(step) {
                    var i = -1;
                    var result = -1;
                    $scope.data.structure.forEach(function (data) {
                        i += 1;
                        if (data == step || data[0] == step) {
                            result = i;
                        }
                    });
                    return result;
                };

                $scope.get_sub_step_index = function(step, subStep) {
                    var i = -1;
                    var result = -1;

                    var stepIndex = $scope.get_step_index(step);

                    $scope.data.structure[stepIndex][1].forEach(function(data){
                        i += 1;
                        if (data == subStep) {
                            result = i;
                        }
                    });
                    return result;
                };

                $scope.get_current_step_index = function () {
                    if(!$scope.data){
                        return -1;
                    }
                    return $scope.get_step_index($scope.data.current_step.step);
                };

                $scope.get_current_sub_step_index = function () {
                    if(!$scope.data){
                        return -1;
                    }
                    return $scope.get_sub_step_index($scope.data.current_step.step, $scope.data.current_step.subStep);
                };

                $scope.get_current_step = function(){
                    return $scope.data.current_step.step;
                };

                $scope.get_current_sub_step = function(){
                    return $scope.data.current_step.subStep;
                };

                $scope.get_first_sub_step_for_step = function(step){
                    var stepIndex = $scope.get_step_index(step);
                    var subSteps = $scope.data.structure[stepIndex][1];
                    return subSteps[0];
                };

                $scope.get_last_sub_step_for_step = function(step){
                    var stepIndex = $scope.get_step_index(step);
                    var subSteps = $scope.data.structure[stepIndex][1];
                    return subSteps[subSteps.length - 1];
                };

                $scope.get_first_sub_step_for_current_step = function(){
                    return $scope.get_first_sub_step_for_step($scope.data.current_step.step)
                };

                $scope.get_last_sub_step_for_current_step = function(step){
                    return $scope.get_last_sub_step_for_step($scope.data.current_step.step)
                };

                $scope.is_last_sub_step_for_current_step = function(){
                    var lastSubStep = $scope.get_last_sub_step_for_step($scope.data.current_step.step)
                    var currentSubStep = $scope.get_current_sub_step();

                    return currentSubStep == lastSubStep;
                };

                $scope.has_more_sub_steps_for_current_step = function(){
                    return !$scope.is_last_sub_step_for_current_step();
                };

                $scope.is_current_sub_step = function(subStep){
                    return subStep == $scope.data.current_step.subStep;
                };

                $scope.get_sub_step = function(subStep){
                    return $scope.data.steps[$scope.data.current_step.step][subStep];
                };

                $scope.get_sub_step_names = function(step){
                    step = step || ($scope.data ? $scope.data.current_step.step : null);
                    if(!step)return [];
                    var stepIndex = $scope.get_step_index(step);
                    var stepData = $scope.data.structure[stepIndex];
                    return stepData[1];
                };

                // Refresh scope
                $scope.refresh();
            },
            templateUrl: getWizardTemplate()
        };
    }]);
})();
