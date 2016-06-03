/**
 * Created by dirk on 17/05/16.
 */

(function() {
    var static_root = $('body').data('staticroot');
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
        var result = {};
        stepNames.forEach(function(stepName){
            var stepInfo = parseStepName(stepName);

            if(stepInfo.subStep == null){
                // Regular item (NOT TESTED)
                result[stepInfo.step] = [];
            }
            else{
                // SubStep item
                if(!result[stepInfo.step]){
                    result[stepInfo.step] = [];
                }
                result[stepInfo.step].push(stepInfo.subStep);
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
        if(data.done){
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

                $scope.action_edit_step = function(subStep, step){
                    step = step || $scope.data.current_step.step;
                    $scope.data.current_step = {
                        step: step,
                        subStep: subStep,
                        fullStep: step + substep_separator + subStep
                    }
                };

                $scope.action_submit_step = function(form_id){
                    var form = $('#' + form_id);
                    var form_data = form.serializeObject();
                    console.log(form_data);

                    var fullStepName = $scope.data.current_step.fullStep;

                    var promise = $http.post(getWizardUrl(fullStepName), form_data);
                    promise.success(function(data){
                        $scope.handle_new_data(data);
                    });
                    promise.error(function(data){
                        $scope.error = true;
                        $scope.handle_new_data(data);
                    });
                };

                $scope.handle_new_data = function(data){
                    data = transformData(data);
                    console.log(data);

                    if(data.done){
                        $scope.handle_done(data);
                        return;
                    }

                    $scope.data = data;
                };

                $scope.handle_done = function(data){
                    var promise = $http.post(getWizardUrl('commit'));
                    promise.success(function(data){
                        console.log(data);
                        var next_url = data.next_url;
                        console.log('next_url:', next_url);
                        window.location = next_url;
                    });
                    promise.error(function(data){
                        $scope.error = true;
                        console.error(data);
                    });
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
                    return $scope.data.structure[step];
                };

                // Refresh scope
                $scope.refresh();
            },
            templateUrl: static_root + 'formtools_addons/templates/directives/wizardapi/wizard.html'
        };
    }]);
})();
