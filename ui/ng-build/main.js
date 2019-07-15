(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["main"],{

/***/ "./src/$$_lazy_route_resource lazy recursive":
/*!**********************************************************!*\
  !*** ./src/$$_lazy_route_resource lazy namespace object ***!
  \**********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

function webpackEmptyAsyncContext(req) {
	// Here Promise.resolve().then() is used instead of new Promise() to prevent
	// uncaught exception popping up in devtools
	return Promise.resolve().then(function() {
		var e = new Error("Cannot find module '" + req + "'");
		e.code = 'MODULE_NOT_FOUND';
		throw e;
	});
}
webpackEmptyAsyncContext.keys = function() { return []; };
webpackEmptyAsyncContext.resolve = webpackEmptyAsyncContext;
module.exports = webpackEmptyAsyncContext;
webpackEmptyAsyncContext.id = "./src/$$_lazy_route_resource lazy recursive";

/***/ }),

/***/ "./src/app/app-routing.module.ts":
/*!***************************************!*\
  !*** ./src/app/app-routing.module.ts ***!
  \***************************************/
/*! exports provided: AppRoutingModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppRoutingModule", function() { return AppRoutingModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _home_home_component__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./home/home.component */ "./src/app/home/home.component.ts");
/* harmony import */ var _scenarios_scenarios_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./scenarios/scenarios.component */ "./src/app/scenarios/scenarios.component.ts");
/* harmony import */ var _scenario_detail_scenario_detail_component__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./scenario-detail/scenario-detail.component */ "./src/app/scenario-detail/scenario-detail.component.ts");
/* harmony import */ var _scenario_new_scenario_new_component__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./scenario-new/scenario-new.component */ "./src/app/scenario-new/scenario-new.component.ts");
/* harmony import */ var _settings_settings_component__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./settings/settings.component */ "./src/app/settings/settings.component.ts");








var appRoutes = [
    { path: 'home', component: _home_home_component__WEBPACK_IMPORTED_MODULE_3__["HomeComponent"] },
    { path: 'scenarios', component: _scenarios_scenarios_component__WEBPACK_IMPORTED_MODULE_4__["ScenariosComponent"] },
    { path: 'scenario/:id', component: _scenario_detail_scenario_detail_component__WEBPACK_IMPORTED_MODULE_5__["ScenarioDetailComponent"] },
    { path: 'scenario-new', component: _scenario_new_scenario_new_component__WEBPACK_IMPORTED_MODULE_6__["ScenarioNewComponent"] },
    { path: 'settings', component: _settings_settings_component__WEBPACK_IMPORTED_MODULE_7__["SettingsComponent"] },
    { path: '',
        redirectTo: '/home',
        pathMatch: 'full'
    },
];
var AppRoutingModule = /** @class */ (function () {
    function AppRoutingModule() {
    }
    AppRoutingModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
            imports: [
                _angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"].forRoot(appRoutes, { enableTracing: true } // <-- debugging purposes only
                )
            ],
            exports: [_angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"]]
        })
    ], AppRoutingModule);
    return AppRoutingModule;
}());



/***/ }),

/***/ "./src/app/app.component.css":
/*!***********************************!*\
  !*** ./src/app/app.component.css ***!
  \***********************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "/*Navbar styling*/\nul {\n  list-style-type: none;\n  margin: 0;\n  padding: 0;\n  overflow: hidden;\n  background-color: midnightblue;\n}\nli {\n  float: left;\n}\nli a {\n  display: block;\n  color: white;\n  text-align: center;\n  padding: 14px 16px;\n  text-decoration: none;\n}\nli a:hover:not(.active) {\n  background-color: lightsteelblue;\n}\n.active-item {\n  background-color: slategrey;\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvYXBwLmNvbXBvbmVudC5jc3MiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUEsaUJBQWlCO0FBQ2pCO0VBQ0UscUJBQXFCO0VBQ3JCLFNBQVM7RUFDVCxVQUFVO0VBQ1YsZ0JBQWdCO0VBQ2hCLDhCQUE4QjtBQUNoQztBQUVBO0VBQ0UsV0FBVztBQUNiO0FBRUE7RUFDRSxjQUFjO0VBQ2QsWUFBWTtFQUNaLGtCQUFrQjtFQUNsQixrQkFBa0I7RUFDbEIscUJBQXFCO0FBQ3ZCO0FBRUE7RUFDRSxnQ0FBZ0M7QUFDbEM7QUFFQTtFQUNFLDJCQUEyQjtBQUM3QiIsImZpbGUiOiJzcmMvYXBwL2FwcC5jb21wb25lbnQuY3NzIiwic291cmNlc0NvbnRlbnQiOlsiLypOYXZiYXIgc3R5bGluZyovXG51bCB7XG4gIGxpc3Qtc3R5bGUtdHlwZTogbm9uZTtcbiAgbWFyZ2luOiAwO1xuICBwYWRkaW5nOiAwO1xuICBvdmVyZmxvdzogaGlkZGVuO1xuICBiYWNrZ3JvdW5kLWNvbG9yOiBtaWRuaWdodGJsdWU7XG59XG5cbmxpIHtcbiAgZmxvYXQ6IGxlZnQ7XG59XG5cbmxpIGEge1xuICBkaXNwbGF5OiBibG9jaztcbiAgY29sb3I6IHdoaXRlO1xuICB0ZXh0LWFsaWduOiBjZW50ZXI7XG4gIHBhZGRpbmc6IDE0cHggMTZweDtcbiAgdGV4dC1kZWNvcmF0aW9uOiBub25lO1xufVxuXG5saSBhOmhvdmVyOm5vdCguYWN0aXZlKSB7XG4gIGJhY2tncm91bmQtY29sb3I6IGxpZ2h0c3RlZWxibHVlO1xufVxuXG4uYWN0aXZlLWl0ZW0ge1xuICBiYWNrZ3JvdW5kLWNvbG9yOiBzbGF0ZWdyZXk7XG59XG4iXX0= */"

/***/ }),

/***/ "./src/app/app.component.html":
/*!************************************!*\
  !*** ./src/app/app.component.html ***!
  \************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<h1>{{title}}</h1>\n\n<nav class=\"navbar\">\n    <div class=\"container\">\n        <ul class=\"nav navbar-nav\">\n            <li class=\"nav-item\" routerLinkActive=\"active-item\">\n              <a class=\"nav-link\" routerLink=\"home\">Home</a>\n            </li>\n            <li class=\"nav-item\" routerLinkActive=\"active-item\">\n              <a class=\"nav-link\" routerLink=\"scenarios\">Scenarios</a>\n            </li>\n            <li class=\"nav-item\" routerLinkActive=\"active-item\"\n                style=\"float:right\">\n              <a class=\"nav-link\" routerLink=\"settings\">Settings</a>\n            </li>\n        </ul>\n    </div>\n</nav>\n\n<router-outlet></router-outlet>\n\n"

/***/ }),

/***/ "./src/app/app.component.ts":
/*!**********************************!*\
  !*** ./src/app/app.component.ts ***!
  \**********************************/
/*! exports provided: AppComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppComponent", function() { return AppComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");


var AppComponent = /** @class */ (function () {
    function AppComponent() {
        this.title = 'Welcome to GridPath';
    }
    AppComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
            selector: 'app-root',
            template: __webpack_require__(/*! ./app.component.html */ "./src/app/app.component.html"),
            styles: [__webpack_require__(/*! ./app.component.css */ "./src/app/app.component.css")]
        })
    ], AppComponent);
    return AppComponent;
}());



/***/ }),

/***/ "./src/app/app.module.ts":
/*!*******************************!*\
  !*** ./src/app/app.module.ts ***!
  \*******************************/
/*! exports provided: AppModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppModule", function() { return AppModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_platform_browser__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/platform-browser */ "./node_modules/@angular/platform-browser/fesm5/platform-browser.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_forms__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @angular/forms */ "./node_modules/@angular/forms/fesm5/forms.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");
/* harmony import */ var _app_routing_module__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./app-routing.module */ "./src/app/app-routing.module.ts");
/* harmony import */ var _app_component__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./app.component */ "./src/app/app.component.ts");
/* harmony import */ var _scenarios_scenarios_component__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./scenarios/scenarios.component */ "./src/app/scenarios/scenarios.component.ts");
/* harmony import */ var _settings_settings_component__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./settings/settings.component */ "./src/app/settings/settings.component.ts");
/* harmony import */ var _scenario_detail_scenario_detail_component__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./scenario-detail/scenario-detail.component */ "./src/app/scenario-detail/scenario-detail.component.ts");
/* harmony import */ var _scenario_new_scenario_new_component__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./scenario-new/scenario-new.component */ "./src/app/scenario-new/scenario-new.component.ts");
/* harmony import */ var _home_home_component__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ./home/home.component */ "./src/app/home/home.component.ts");



 // <-- NgModel lives here









var AppModule = /** @class */ (function () {
    function AppModule() {
    }
    AppModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_2__["NgModule"])({
            declarations: [
                _app_component__WEBPACK_IMPORTED_MODULE_6__["AppComponent"],
                _scenarios_scenarios_component__WEBPACK_IMPORTED_MODULE_7__["ScenariosComponent"],
                _settings_settings_component__WEBPACK_IMPORTED_MODULE_8__["SettingsComponent"],
                _scenario_detail_scenario_detail_component__WEBPACK_IMPORTED_MODULE_9__["ScenarioDetailComponent"],
                _scenario_new_scenario_new_component__WEBPACK_IMPORTED_MODULE_10__["ScenarioNewComponent"],
                _home_home_component__WEBPACK_IMPORTED_MODULE_11__["HomeComponent"]
            ],
            imports: [
                _angular_platform_browser__WEBPACK_IMPORTED_MODULE_1__["BrowserModule"],
                _angular_forms__WEBPACK_IMPORTED_MODULE_3__["FormsModule"],
                _angular_common_http__WEBPACK_IMPORTED_MODULE_4__["HttpClientModule"],
                _app_routing_module__WEBPACK_IMPORTED_MODULE_5__["AppRoutingModule"],
                _angular_forms__WEBPACK_IMPORTED_MODULE_3__["ReactiveFormsModule"]
            ],
            providers: [],
            bootstrap: [_app_component__WEBPACK_IMPORTED_MODULE_6__["AppComponent"]]
        })
    ], AppModule);
    return AppModule;
}());



/***/ }),

/***/ "./src/app/home/home.component.css":
/*!*****************************************!*\
  !*** ./src/app/home/home.component.css ***!
  \*****************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IiIsImZpbGUiOiJzcmMvYXBwL2hvbWUvaG9tZS5jb21wb25lbnQuY3NzIn0= */"

/***/ }),

/***/ "./src/app/home/home.component.html":
/*!******************************************!*\
  !*** ./src/app/home/home.component.html ***!
  \******************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div><span>Server Status: </span>{{serverStatus}}</div>\n<button id=\"checkServerStatusClick\" class=\"button-primary\"\n            (click)=\"updateServerStatus()\">Update server status</button>\n"

/***/ }),

/***/ "./src/app/home/home.component.ts":
/*!****************************************!*\
  !*** ./src/app/home/home.component.ts ***!
  \****************************************/
/*! exports provided: HomeComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "HomeComponent", function() { return HomeComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _home_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./home.service */ "./src/app/home/home.service.ts");



var electron = window.require('electron');
var HomeComponent = /** @class */ (function () {
    function HomeComponent(homeService) {
        this.homeService = homeService;
    }
    HomeComponent.prototype.ngOnInit = function () {
        this.getServerStatus();
        console.log(this.serverStatus);
    };
    HomeComponent.prototype.getServerStatus = function () {
        var _this = this;
        console.log("Getting server status...");
        this.homeService.getScenarios()
            .subscribe(function (status) { return _this.serverStatus = status; }, function (error) {
            console.log('HTTP Error caught', error);
            _this.serverStatus = 'down';
        });
    };
    HomeComponent.prototype.updateServerStatus = function (event) {
        console.log('Updating server status...');
        this.getServerStatus();
    };
    HomeComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
            selector: 'app-home',
            template: __webpack_require__(/*! ./home.component.html */ "./src/app/home/home.component.html"),
            styles: [__webpack_require__(/*! ./home.component.css */ "./src/app/home/home.component.css")]
        }),
        tslib__WEBPACK_IMPORTED_MODULE_0__["__metadata"]("design:paramtypes", [_home_service__WEBPACK_IMPORTED_MODULE_2__["HomeService"]])
    ], HomeComponent);
    return HomeComponent;
}());



/***/ }),

/***/ "./src/app/home/home.service.ts":
/*!**************************************!*\
  !*** ./src/app/home/home.service.ts ***!
  \**************************************/
/*! exports provided: HomeService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "HomeService", function() { return HomeService; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");



var HomeService = /** @class */ (function () {
    function HomeService(http) {
        this.http = http;
        this.statusURL = 'http://127.0.0.1:8080/server-status';
    }
    HomeService.prototype.getScenarios = function () {
        console.log(this.http.get(this.statusURL));
        return (this.http.get(this.statusURL));
    };
    HomeService = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Injectable"])({
            providedIn: 'root'
        }),
        tslib__WEBPACK_IMPORTED_MODULE_0__["__metadata"]("design:paramtypes", [_angular_common_http__WEBPACK_IMPORTED_MODULE_2__["HttpClient"]])
    ], HomeService);
    return HomeService;
}());



/***/ }),

/***/ "./src/app/scenario-detail/scenario-detail.component.css":
/*!***************************************************************!*\
  !*** ./src/app/scenario-detail/scenario-detail.component.css ***!
  \***************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "/* scenarioDetailComponent's private CSS styles */\n\n.scenario-detail th {\n  background-color: midnightblue;\n  color: white;\n}\n\n.scenario-detail th, td {\n    padding: 5px;\n    text-align: left;\n}\n\n.scenario-detail tr:nth-child(odd) {\n  background-color: #f2f2f2;\n}\n\n.scenario-detail td:first-child {\n  background-color: lightsteelblue;\n}\n\n.scenario-detail caption {\n  font-weight: bold;\n  text-align: left;\n  margin-top: 10px;\n  margin-bottom: 1px;\n}\n\n.button-primary {\n  background:aliceblue;\n  color:midnightblue;\n  font-size: medium;\n  font-weight: bold;\n  margin-top: 10px;\n  padding: 5px 10px;\n  cursor:pointer\n}\n\n.button-primary:hover {\n  background-color: darkblue;\n  color: white\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvc2NlbmFyaW8tZGV0YWlsL3NjZW5hcmlvLWRldGFpbC5jb21wb25lbnQuY3NzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBLGlEQUFpRDs7QUFFakQ7RUFDRSw4QkFBOEI7RUFDOUIsWUFBWTtBQUNkOztBQUVBO0lBQ0ksWUFBWTtJQUNaLGdCQUFnQjtBQUNwQjs7QUFFQTtFQUNFLHlCQUF5QjtBQUMzQjs7QUFFQTtFQUNFLGdDQUFnQztBQUNsQzs7QUFFQTtFQUNFLGlCQUFpQjtFQUNqQixnQkFBZ0I7RUFDaEIsZ0JBQWdCO0VBQ2hCLGtCQUFrQjtBQUNwQjs7QUFFQTtFQUNFLG9CQUFvQjtFQUNwQixrQkFBa0I7RUFDbEIsaUJBQWlCO0VBQ2pCLGlCQUFpQjtFQUNqQixnQkFBZ0I7RUFDaEIsaUJBQWlCO0VBQ2pCO0FBQ0Y7O0FBRUE7RUFDRSwwQkFBMEI7RUFDMUI7QUFDRiIsImZpbGUiOiJzcmMvYXBwL3NjZW5hcmlvLWRldGFpbC9zY2VuYXJpby1kZXRhaWwuY29tcG9uZW50LmNzcyIsInNvdXJjZXNDb250ZW50IjpbIi8qIHNjZW5hcmlvRGV0YWlsQ29tcG9uZW50J3MgcHJpdmF0ZSBDU1Mgc3R5bGVzICovXG5cbi5zY2VuYXJpby1kZXRhaWwgdGgge1xuICBiYWNrZ3JvdW5kLWNvbG9yOiBtaWRuaWdodGJsdWU7XG4gIGNvbG9yOiB3aGl0ZTtcbn1cblxuLnNjZW5hcmlvLWRldGFpbCB0aCwgdGQge1xuICAgIHBhZGRpbmc6IDVweDtcbiAgICB0ZXh0LWFsaWduOiBsZWZ0O1xufVxuXG4uc2NlbmFyaW8tZGV0YWlsIHRyOm50aC1jaGlsZChvZGQpIHtcbiAgYmFja2dyb3VuZC1jb2xvcjogI2YyZjJmMjtcbn1cblxuLnNjZW5hcmlvLWRldGFpbCB0ZDpmaXJzdC1jaGlsZCB7XG4gIGJhY2tncm91bmQtY29sb3I6IGxpZ2h0c3RlZWxibHVlO1xufVxuXG4uc2NlbmFyaW8tZGV0YWlsIGNhcHRpb24ge1xuICBmb250LXdlaWdodDogYm9sZDtcbiAgdGV4dC1hbGlnbjogbGVmdDtcbiAgbWFyZ2luLXRvcDogMTBweDtcbiAgbWFyZ2luLWJvdHRvbTogMXB4O1xufVxuXG4uYnV0dG9uLXByaW1hcnkge1xuICBiYWNrZ3JvdW5kOmFsaWNlYmx1ZTtcbiAgY29sb3I6bWlkbmlnaHRibHVlO1xuICBmb250LXNpemU6IG1lZGl1bTtcbiAgZm9udC13ZWlnaHQ6IGJvbGQ7XG4gIG1hcmdpbi10b3A6IDEwcHg7XG4gIHBhZGRpbmc6IDVweCAxMHB4O1xuICBjdXJzb3I6cG9pbnRlclxufVxuXG4uYnV0dG9uLXByaW1hcnk6aG92ZXIge1xuICBiYWNrZ3JvdW5kLWNvbG9yOiBkYXJrYmx1ZTtcbiAgY29sb3I6IHdoaXRlXG59XG4iXX0= */"

/***/ }),

/***/ "./src/app/scenario-detail/scenario-detail.component.html":
/*!****************************************************************!*\
  !*** ./src/app/scenario-detail/scenario-detail.component.html ***!
  \****************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<h2>{{scenarioDetail[1].value}}<span> Scenario Details</span></h2>\n\n<table class=\"scenario-detail\">\n  <caption>Features</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailFeatures\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Temporal settings</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailTemporal\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Load zone settings</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailGeographyLoadZones\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>System Load</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailLoad\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Project capacity settings</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailProjectCapacity\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Project operating characteristics settings</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailProjectOpChars\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Fuels settings</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailFuels\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Transmission capacity settings</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailTransmissionCapacity\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Transmission operating characteristics settings</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailTransmissionOpChars\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Transmission hurdle rates</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailTransmissionHurdleRates\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Transmission simultaneous flow limits</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailTransmissionSimFlow\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Load Following Reserves Up</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailLFUp\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Load Following Reserves Down</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailLFDown\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Regulation Reserves Up</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailRegUp\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Regulation Reserves Down</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailRegDown\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Spinning Reserves</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailSpin\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Frequency Response Reserves</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailFreqResp\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>RPS</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailRPS\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Carbon Cap</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailCarbonCap\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>PRM</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailPRM\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<table class=\"scenario-detail\">\n  <caption>Local Capacity</caption>\n<tr>\n<th>Name</th>\n<th>Value</th>\n</tr>\n  <ng-container *ngFor=\"let sd of scenarioDetailLocalCapacity\">\n     <tr>\n       <td>{{sd.name}}</td>\n       <td>{{sd.value}}</td>\n     </tr>\n  </ng-container>\n</table>\n\n<button id=\"runScenarioButton\" class=\"button-primary\"\n      (click)=\"runScenario(scenarioDetail[0].value)\">Run Scenario</button>\n"

/***/ }),

/***/ "./src/app/scenario-detail/scenario-detail.component.ts":
/*!**************************************************************!*\
  !*** ./src/app/scenario-detail/scenario-detail.component.ts ***!
  \**************************************************************/
/*! exports provided: ScenarioDetailComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScenarioDetailComponent", function() { return ScenarioDetailComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _angular_common__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @angular/common */ "./node_modules/@angular/common/fesm5/common.js");
/* harmony import */ var _scenario_detail_service__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./scenario-detail.service */ "./src/app/scenario-detail/scenario-detail.service.ts");




var electron = window.require('electron');

var ScenarioDetailComponent = /** @class */ (function () {
    function ScenarioDetailComponent(route, scenarioDetailService, location) {
        this.route = route;
        this.scenarioDetailService = scenarioDetailService;
        this.location = location;
    }
    ScenarioDetailComponent.prototype.ngOnInit = function () {
        var _this = this;
        // The ActivatedRoute service provides a params Observable which we can
        // subscribe to in order to get the route parameters
        this.sub = this.route.params.subscribe(function (params) {
            _this.id = +params['id'];
            console.log("Scenario ID is " + _this.id);
        });
        this.getScenarioDetailAll(this.id);
        this.getScenarioDetailFeatures(this.id);
        this.getScenarioDetailTemporal(this.id);
        this.getScenarioDetailGeographyLoadZones(this.id);
        this.getScenarioDetailLoad(this.id);
        this.getScenarioDetailProjectCapacity(this.id);
        this.getScenarioDetailProjectOpChars(this.id);
        this.getScenarioDetailFuels(this.id);
        this.getScenarioDetailTransmissionCapacity(this.id);
        this.getScenarioDetailTransmissionOpChars(this.id);
        this.getScenarioDetailTransmissionHurdleRates(this.id);
        this.getScenarioDetailTransmissionSimFlow(this.id);
        this.getScenarioDetailLFup(this.id);
        this.getScenarioDetailLFDown(this.id);
        this.getScenarioDetailRegUp(this.id);
        this.getScenarioDetailRegDown(this.id);
        this.getScenarioDetailSpin(this.id);
        this.getScenarioDetailFreqResp(this.id);
        this.getScenarioDetailRPS(this.id);
        this.getScenarioDetailCarbonCap(this.id);
        this.getScenarioDetailPRM(this.id);
        this.getScenarioDetailLocalCapacity(this.id);
    };
    ScenarioDetailComponent.prototype.getScenarioDetailAll = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailAll(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetail = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailFeatures = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailFeatures(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailFeatures = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailTemporal = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailTemporal(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailTemporal = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailGeographyLoadZones = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailGeographyLoadZones(id)
            .subscribe(function (scenarioDetail) {
            return _this.scenarioDetailGeographyLoadZones = scenarioDetail;
        });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailLoad = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailLoad(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailLoad = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailProjectCapacity = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailProjectCapacity(id)
            .subscribe(function (scenarioDetail) {
            return _this.scenarioDetailProjectCapacity = scenarioDetail;
        });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailProjectOpChars = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailProjectOpChars(id)
            .subscribe(function (scenarioDetail) {
            return _this.scenarioDetailProjectOpChars = scenarioDetail;
        });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailFuels = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailFuels(id)
            .subscribe(function (scenarioDetail) {
            return _this.scenarioDetailFuels = scenarioDetail;
        });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailTransmissionCapacity = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailTransmissionCapacity(id)
            .subscribe(function (scenarioDetail) {
            return _this.scenarioDetailTransmissionCapacity = scenarioDetail;
        });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailTransmissionOpChars = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailTransmissionOpChars(id)
            .subscribe(function (scenarioDetail) {
            return _this.scenarioDetailTransmissionOpChars = scenarioDetail;
        });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailTransmissionHurdleRates = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailTransmissionHurdleRates(id)
            .subscribe(function (scenarioDetail) {
            return _this.scenarioDetailTransmissionHurdleRates = scenarioDetail;
        });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailTransmissionSimFlow = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailTransmissionSimFlow(id)
            .subscribe(function (scenarioDetail) {
            return _this.scenarioDetailTransmissionSimFlow = scenarioDetail;
        });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailLFup = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailLFUp(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailLFUp = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailLFDown = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailLFDown(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailLFDown = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailRegUp = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailRegUp(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailRegUp = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailRegDown = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailRegDown(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailRegDown = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailSpin = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailSpin(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailSpin = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailFreqResp = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailFreqResp(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailFreqResp = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailRPS = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailRPS(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailRPS = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailCarbonCap = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailCarbonCap(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailCarbonCap = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailPRM = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailPRM(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailPRM = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.getScenarioDetailLocalCapacity = function (id) {
        var _this = this;
        this.scenarioDetailService.getScenarioDetailLocalCapacity(id)
            .subscribe(function (scenarioDetail) { return _this.scenarioDetailLocalCapacity = scenarioDetail; });
    };
    ScenarioDetailComponent.prototype.goBack = function () {
        this.location.back();
    };
    ScenarioDetailComponent.prototype.runScenario = function (id) {
        console.log("Running scenario " + id);
        electron.ipcRenderer.send('runScenario', id);
    };
    ScenarioDetailComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
            selector: 'app-scenario-detail',
            template: __webpack_require__(/*! ./scenario-detail.component.html */ "./src/app/scenario-detail/scenario-detail.component.html"),
            styles: [__webpack_require__(/*! ./scenario-detail.component.css */ "./src/app/scenario-detail/scenario-detail.component.css")]
        }),
        tslib__WEBPACK_IMPORTED_MODULE_0__["__metadata"]("design:paramtypes", [_angular_router__WEBPACK_IMPORTED_MODULE_2__["ActivatedRoute"],
            _scenario_detail_service__WEBPACK_IMPORTED_MODULE_4__["ScenarioDetailService"],
            _angular_common__WEBPACK_IMPORTED_MODULE_3__["Location"]])
    ], ScenarioDetailComponent);
    return ScenarioDetailComponent;
}());



/***/ }),

/***/ "./src/app/scenario-detail/scenario-detail.service.ts":
/*!************************************************************!*\
  !*** ./src/app/scenario-detail/scenario-detail.service.ts ***!
  \************************************************************/
/*! exports provided: ScenarioDetailService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScenarioDetailService", function() { return ScenarioDetailService; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");



var ScenarioDetailService = /** @class */ (function () {
    function ScenarioDetailService(http) {
        this.http = http;
        this.scenariosBaseURL = 'http://127.0.0.1:8080/scenarios/';
    }
    ScenarioDetailService.prototype.getScenarioDetailAll = function (id) {
        console.log("" + this.scenariosBaseURL + id);
        return this.http.get("" + this.scenariosBaseURL + id);
    };
    ScenarioDetailService.prototype.getScenarioDetailFeatures = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/features");
    };
    ScenarioDetailService.prototype.getScenarioDetailTemporal = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/temporal");
    };
    ScenarioDetailService.prototype.getScenarioDetailGeographyLoadZones = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/geography-load-zones");
    };
    ScenarioDetailService.prototype.getScenarioDetailProjectCapacity = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/project-capacity");
    };
    ScenarioDetailService.prototype.getScenarioDetailProjectOpChars = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/project-opchars");
    };
    ScenarioDetailService.prototype.getScenarioDetailFuels = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/fuels");
    };
    ScenarioDetailService.prototype.getScenarioDetailTransmissionCapacity = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/transmission-capacity");
    };
    ScenarioDetailService.prototype.getScenarioDetailTransmissionOpChars = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/transmission-opchars");
    };
    ScenarioDetailService.prototype.getScenarioDetailTransmissionHurdleRates = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/transmission-hurdle-rates");
    };
    ScenarioDetailService.prototype.getScenarioDetailTransmissionSimFlow = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/transmission-sim-flow");
    };
    ScenarioDetailService.prototype.getScenarioDetailLoad = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/load");
    };
    ScenarioDetailService.prototype.getScenarioDetailLFUp = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/lf-up");
    };
    ScenarioDetailService.prototype.getScenarioDetailLFDown = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/lf-down");
    };
    ScenarioDetailService.prototype.getScenarioDetailRegUp = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/reg-up");
    };
    ScenarioDetailService.prototype.getScenarioDetailRegDown = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/reg-down");
    };
    ScenarioDetailService.prototype.getScenarioDetailSpin = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/spin");
    };
    ScenarioDetailService.prototype.getScenarioDetailFreqResp = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/freq-resp");
    };
    ScenarioDetailService.prototype.getScenarioDetailRPS = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/rps");
    };
    ScenarioDetailService.prototype.getScenarioDetailCarbonCap = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/carbon-cap");
    };
    ScenarioDetailService.prototype.getScenarioDetailPRM = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/prm");
    };
    ScenarioDetailService.prototype.getScenarioDetailLocalCapacity = function (id) {
        return this.http.get("" + this.scenariosBaseURL + id + "/local-capacity");
    };
    ScenarioDetailService = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Injectable"])({
            providedIn: 'root'
        }),
        tslib__WEBPACK_IMPORTED_MODULE_0__["__metadata"]("design:paramtypes", [_angular_common_http__WEBPACK_IMPORTED_MODULE_2__["HttpClient"]])
    ], ScenarioDetailService);
    return ScenarioDetailService;
}());



/***/ }),

/***/ "./src/app/scenario-new/scenario-new.component.css":
/*!*********************************************************!*\
  !*** ./src/app/scenario-new/scenario-new.component.css ***!
  \*********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "/* scenarioNewComponent's private CSS styles */\n\n.scenario-detail th {\n  background-color: midnightblue;\n  color: white;\n}\n\n.scenario-detail th, td {\n    padding: 5px;\n    text-align: left;\n}\n\n.scenario-detail tr:nth-child(odd) {\n  background-color: #f2f2f2;\n}\n\n.scenario-detail td:first-child {\n  background-color: lightsteelblue;\n}\n\n.scenario-detail caption {\n  font-weight: bold;\n  text-align: left;\n  margin-top: 10px;\n  margin-bottom: 1px;\n}\n\n.button-primary {\n  background:aliceblue;\n  color:midnightblue;\n  font-size: medium;\n  font-weight: bold;\n  margin-top: 10px;\n  padding: 5px 10px;\n  cursor:pointer\n}\n\n.button-primary:hover {\n  background-color: darkblue;\n  color: white\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvc2NlbmFyaW8tbmV3L3NjZW5hcmlvLW5ldy5jb21wb25lbnQuY3NzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBLDhDQUE4Qzs7QUFFOUM7RUFDRSw4QkFBOEI7RUFDOUIsWUFBWTtBQUNkOztBQUVBO0lBQ0ksWUFBWTtJQUNaLGdCQUFnQjtBQUNwQjs7QUFFQTtFQUNFLHlCQUF5QjtBQUMzQjs7QUFFQTtFQUNFLGdDQUFnQztBQUNsQzs7QUFFQTtFQUNFLGlCQUFpQjtFQUNqQixnQkFBZ0I7RUFDaEIsZ0JBQWdCO0VBQ2hCLGtCQUFrQjtBQUNwQjs7QUFFQTtFQUNFLG9CQUFvQjtFQUNwQixrQkFBa0I7RUFDbEIsaUJBQWlCO0VBQ2pCLGlCQUFpQjtFQUNqQixnQkFBZ0I7RUFDaEIsaUJBQWlCO0VBQ2pCO0FBQ0Y7O0FBRUE7RUFDRSwwQkFBMEI7RUFDMUI7QUFDRiIsImZpbGUiOiJzcmMvYXBwL3NjZW5hcmlvLW5ldy9zY2VuYXJpby1uZXcuY29tcG9uZW50LmNzcyIsInNvdXJjZXNDb250ZW50IjpbIi8qIHNjZW5hcmlvTmV3Q29tcG9uZW50J3MgcHJpdmF0ZSBDU1Mgc3R5bGVzICovXG5cbi5zY2VuYXJpby1kZXRhaWwgdGgge1xuICBiYWNrZ3JvdW5kLWNvbG9yOiBtaWRuaWdodGJsdWU7XG4gIGNvbG9yOiB3aGl0ZTtcbn1cblxuLnNjZW5hcmlvLWRldGFpbCB0aCwgdGQge1xuICAgIHBhZGRpbmc6IDVweDtcbiAgICB0ZXh0LWFsaWduOiBsZWZ0O1xufVxuXG4uc2NlbmFyaW8tZGV0YWlsIHRyOm50aC1jaGlsZChvZGQpIHtcbiAgYmFja2dyb3VuZC1jb2xvcjogI2YyZjJmMjtcbn1cblxuLnNjZW5hcmlvLWRldGFpbCB0ZDpmaXJzdC1jaGlsZCB7XG4gIGJhY2tncm91bmQtY29sb3I6IGxpZ2h0c3RlZWxibHVlO1xufVxuXG4uc2NlbmFyaW8tZGV0YWlsIGNhcHRpb24ge1xuICBmb250LXdlaWdodDogYm9sZDtcbiAgdGV4dC1hbGlnbjogbGVmdDtcbiAgbWFyZ2luLXRvcDogMTBweDtcbiAgbWFyZ2luLWJvdHRvbTogMXB4O1xufVxuXG4uYnV0dG9uLXByaW1hcnkge1xuICBiYWNrZ3JvdW5kOmFsaWNlYmx1ZTtcbiAgY29sb3I6bWlkbmlnaHRibHVlO1xuICBmb250LXNpemU6IG1lZGl1bTtcbiAgZm9udC13ZWlnaHQ6IGJvbGQ7XG4gIG1hcmdpbi10b3A6IDEwcHg7XG4gIHBhZGRpbmc6IDVweCAxMHB4O1xuICBjdXJzb3I6cG9pbnRlclxufVxuXG4uYnV0dG9uLXByaW1hcnk6aG92ZXIge1xuICBiYWNrZ3JvdW5kLWNvbG9yOiBkYXJrYmx1ZTtcbiAgY29sb3I6IHdoaXRlXG59XG4iXX0= */"

/***/ }),

/***/ "./src/app/scenario-new/scenario-new.component.html":
/*!**********************************************************!*\
  !*** ./src/app/scenario-new/scenario-new.component.html ***!
  \**********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<h2><span>New Scenario: </span>{{newScenarioForm.value.scenarioName}}</h2>\n\n<form [formGroup]=\"newScenarioForm\" (ngSubmit)=\"saveNewScenario()\">\n\n  <p><label>\n  Scenario Name:\n  <input type=\"text\" formControlName=\"scenarioName\">\n</label></p>\n\n  <p><label>\n  Description:\n  <input type=\"text\" formControlName=\"scenarioDescription\">\n</label></p>\n\n\n<table class=\"scenario-detail\">\n  <caption>Features</caption>\n    <tr>\n      <th>Name</th>\n      <th>Value</th>\n    </tr>\n      <ng-container *ngFor=\"let sd of features\">\n         <tr>\n           <td>{{sd.featureName}}</td>\n           <td>\n             <select formControlName=\"{{sd.formControlName}}\">\n                <option *ngFor=\"let selectionOption of featureSelectionOption\">\n                  {{selectionOption}}\n                </option>\n              </select>\n           </td>\n         </tr>\n      </ng-container>\n</table>\n\n<ng-container *ngFor=\"let tbl of ScenarioNewStructure\">\n  <table class=\"scenario-detail\">\n    <caption>{{tbl.tableCaption}}</caption>\n        <tr>\n          <th>Name</th>\n          <th>Value</th>\n        </tr>\n      <ng-container *ngFor=\"let tblRow of tbl.settingRows\">\n         <tr>\n           <td>{{tblRow.rowName}}</td>\n           <td>\n             <select formControlName=\"{{tblRow.rowFormControlName}}\">\n                <option value=\"\"></option>\n                <option *ngFor=\"let settingOption of tblRow.settingOptions\">\n                  {{settingOption.name}}\n                </option>\n              </select>\n           </td>\n        </tr>\n      </ng-container>\n  </table>\n</ng-container>\n\n<button class=\"button-primary\">Validate Scenario (inactive)</button>\n\n<button type=\"submit\" [disabled]=\"!newScenarioForm.valid\"\n        class=\"button-primary\">\n  Save Scenario</button>\n</form>\n"

/***/ }),

/***/ "./src/app/scenario-new/scenario-new.component.ts":
/*!********************************************************!*\
  !*** ./src/app/scenario-new/scenario-new.component.ts ***!
  \********************************************************/
/*! exports provided: ScenarioNewComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScenarioNewComponent", function() { return ScenarioNewComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_forms__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/forms */ "./node_modules/@angular/forms/fesm5/forms.js");
/* harmony import */ var _scenario_new_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./scenario-new.service */ "./src/app/scenario-new/scenario-new.service.ts");



var io = window.require('socket.io-client');

var ScenarioNewComponent = /** @class */ (function () {
    function ScenarioNewComponent(scenarioNewService) {
        this.scenarioNewService = scenarioNewService;
        // Create the form
        this.newScenarioForm = new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormGroup"]({
            scenarioName: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            scenarioDescription: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureFuels: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureTransmission: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureTransmissionHurdleRates: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureSimFlowLimits: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureLFUp: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureLFDown: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureRegUp: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureRegDown: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureSpin: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureFreqResp: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureRPS: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureCarbonCap: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureTrackCarbonImports: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featurePRM: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureELCCSurface: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            featureLocalCapacity: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            temporalSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyLoadZonesSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyProjectLoadZonesSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyTxLoadZonesSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            systemLoadSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectPortfolioSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectExistingCapacitySetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectExistingFixedCostSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectNewCostSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectNewPotentialSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectAvailabilitySetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectOperationalCharsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectFuelsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            fuelPricesSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            transmissionPortfolioSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            transmissionExistingCapacitySetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            transmissionOperationalCharsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            transmissionHurdleRatesSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            transmissionSimultaneousFlowLimitsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            transmissionSimultaneousFlowLimitLineGroupsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyLoadFollowingUpBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            loadFollowingUpRequirementSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectLoadFollowingUpBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyLoadFollowingDownBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            loadFollowingDownRequirementSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectLoadFollowingDownBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyRegulationUpBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            regulationUpRequirementSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectRegulationUpBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyRegulationDownBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            regulationDownRequirementSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectRegulationDownBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographySpinningReservesBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            spinningReservesRequirementSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectSpinningReservesBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyFrequencyResponseBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            frequencyResponseRequirementSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectFrequencyResponseBAsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyRPSAreasSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            rpsTargetSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectRPSAreasSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyCarbonCapAreasSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            carbonCapTargetSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectCarbonCapAreasSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            transmissionCarbonCapAreasSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyPRMAreasSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            prmRequirementSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectPRMAreasSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectELCCCharsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            elccSurfaceSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectPRMEnergyOnlySetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            geographyLocalCapacityAreasSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            localCapacityRequirementSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectLocalCapacityAreasSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            projectLocalCapacityCharsSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"](''),
            tuningSetting: new _angular_forms__WEBPACK_IMPORTED_MODULE_2__["FormControl"]('')
        });
        this.features = [];
        var featureFuels = new Feature();
        featureFuels.featureName = 'feature_fuels';
        featureFuels.formControlName = 'featureFuels';
        this.features.push(featureFuels);
        var featureTransmission = new Feature();
        featureTransmission.featureName = 'feature_transmission';
        featureTransmission.formControlName = 'featureTransmission';
        this.features.push(featureTransmission);
        var featureTransmissionHurdleRates = new Feature();
        featureTransmissionHurdleRates.featureName =
            'feature_transmission_hurdle_rates';
        featureTransmissionHurdleRates.formControlName =
            'featureTransmissionHurdleRates';
        this.features.push(featureTransmissionHurdleRates);
        var featureSimFlowLimits = new Feature();
        featureSimFlowLimits.featureName = 'feature_simultaneous_flow_limits';
        featureSimFlowLimits.formControlName = 'featureSimFlowLimits';
        this.features.push(featureSimFlowLimits);
        var featureLFUp = new Feature();
        featureLFUp.featureName = 'feature_load_following_up';
        featureLFUp.formControlName = 'featureLFUp';
        this.features.push(featureLFUp);
        var featureLFDown = new Feature();
        featureLFDown.featureName = 'feature_load_following_down';
        featureLFDown.formControlName = 'featureLFDown';
        this.features.push(featureLFDown);
        var featureRegDown = new Feature();
        featureRegDown.featureName = 'feature_regulation_down';
        featureRegDown.formControlName = 'featureRegDown';
        this.features.push(featureRegDown);
        var featureRegUp = new Feature();
        featureRegUp.featureName = 'feature_regulation_up';
        featureRegUp.formControlName = 'featureRegUp';
        this.features.push(featureRegUp);
        var featureSpin = new Feature();
        featureSpin.featureName = 'feature_spinning_reserves';
        featureSpin.formControlName = 'featureSpin';
        this.features.push(featureSpin);
        var featureFreqResp = new Feature();
        featureFreqResp.featureName = 'feature_frequency_response';
        featureFreqResp.formControlName = 'featureFreqResp';
        this.features.push(featureFreqResp);
        var featureRPS = new Feature();
        featureRPS.featureName = 'feature_rps';
        featureRPS.formControlName = 'featureRPS';
        this.features.push(featureRPS);
        var featureCarbonCap = new Feature();
        featureCarbonCap.featureName = 'feature_carbon_cap';
        featureCarbonCap.formControlName = 'featureCarbonCap';
        this.features.push(featureCarbonCap);
        var featureTrackCarbonImports = new Feature();
        featureTrackCarbonImports.featureName = 'feature_track_carbon_imports';
        featureTrackCarbonImports.formControlName = 'featureTrackCarbonImports';
        this.features.push(featureTrackCarbonImports);
        var featurePRM = new Feature();
        featurePRM.featureName = 'feature_prm';
        featurePRM.formControlName = 'featurePRM';
        this.features.push(featurePRM);
        var featureELCCSurface = new Feature();
        featureELCCSurface.featureName = 'feature_elcc_surface';
        featureELCCSurface.formControlName = 'featureELCCSurface';
        this.features.push(featureELCCSurface);
        var featureLocalCapacity = new Feature();
        featureLocalCapacity.featureName = 'feature_local_capacity';
        featureLocalCapacity.formControlName = 'featureLocalCapacity';
        this.features.push(featureLocalCapacity);
        this.featureSelectionOption = featureSelectionOptions();
    }
    ScenarioNewComponent.prototype.ngOnInit = function () {
        this.ScenarioNewStructure = [];
        this.getSettingOptionsTemporal();
        this.getSettingOptionsLoadZones();
        this.getSettingOptionsLoad();
        this.getSettingOptionsProjectCapacity();
        this.getSettingOptionsProjectOperationalChars();
        this.getSettingOptionsFuels();
        this.getSettingOptionsTransmissionCapacity();
        this.getSettingOptionsTransmissionOperationalChars();
        this.getSettingOptionsTransmissionHurdleRates();
        this.getSettingOptionsTransmissionSimultaneousFlowLimits();
        this.getSettingOptionsLFReservesUp();
        this.getSettingOptionsLFReservesDown();
        this.getSettingOptionsRegulationUp();
        this.getSettingOptionsRegulationDown();
        this.getSettingOptionsSpinningReserves();
        this.getSettingOptionsFrequencyResponse();
        this.getSettingOptionsRPS();
        this.getSettingOptionsCarbonCap();
        this.getSettingOptionsPRM();
        this.getSettingOptionsLocalCapacity();
        this.getSettingOptionsTuning();
    };
    ScenarioNewComponent.prototype.getSettingOptionsTemporal = function () {
        var _this = this;
        // Set the setting table captions
        this.temporalSettingsTable = new SettingsTable();
        this.temporalSettingsTable.tableCaption = 'Temporal settings';
        this.temporalSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingTemporal()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.temporalSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('temporal', 'temporalSetting', _this.temporalSettingOptions);
            // Add the row to the table
            _this.temporalSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.temporalSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsLoadZones = function () {
        var _this = this;
        // Set the setting table captions
        this.loadZoneSettingsTable = new SettingsTable();
        this.loadZoneSettingsTable.tableCaption = 'Load zone settings';
        this.loadZoneSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingLoadZones()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyLoadZonesSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('geography_load_zones', 'geographyLoadZonesSetting', _this.geographyLoadZonesSettingOptions);
            // Add the row to the table
            _this.loadZoneSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectLoadZones()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectLoadZonesSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_load_zones', 'geographyProjectLoadZonesSetting', _this.projectLoadZonesSettingOptions);
            // Add the row to the table
            _this.loadZoneSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingTransmissionLoadZones()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.transmissionLoadZonesSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('transmission_load_zones', 'geographyTxLoadZonesSetting', _this.transmissionLoadZonesSettingOptions);
            // Add the row to the table
            _this.loadZoneSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.loadZoneSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsLoad = function () {
        var _this = this;
        // Set the setting table captions
        this.systemLoadSettingsTable = new SettingsTable();
        this.systemLoadSettingsTable.tableCaption = 'System load';
        this.systemLoadSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingSystemLoad()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.systemLoadSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('load_profile', 'systemLoadSetting', _this.systemLoadSettingOptions);
            // Add the row to the table
            _this.systemLoadSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.systemLoadSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsProjectCapacity = function () {
        var _this = this;
        // Set the setting table captions
        this.projectCapacitySettingsTable = new SettingsTable();
        this.projectCapacitySettingsTable.tableCaption = 'Project capacity';
        this.projectCapacitySettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingProjectPortfolio()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectPortfolioSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_portfolio', 'projectPortfolioSetting', _this.projectPortfolioSettingOptions);
            // Add the row to the table
            _this.projectCapacitySettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectExistingCapacity()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectExistingCapacitySettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_existing_capacity', 'projectExistingCapacitySetting', _this.projectExistingCapacitySettingOptions);
            // Add the row to the table
            _this.projectCapacitySettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectExistingFixedCost()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectExistingFixedCostSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_existing_fixed_cost', 'projectExistingFixedCostSetting', _this.projectExistingFixedCostSettingOptions);
            // Add the row to the table
            _this.projectCapacitySettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectNewCost()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectNewCostSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_new_cost', 'projectNewCostSetting', _this.projectNewCostSettingOptions);
            // Add the row to the table
            _this.projectCapacitySettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectNewPotential()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectNewPotentialSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_new_potential', 'projectNewPotentialSetting', _this.projectNewPotentialSettingOptions);
            // Add the row to the table
            _this.projectCapacitySettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectAvailability()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectAvailabilitySettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_availability', 'projectAvailabilitySetting', _this.projectAvailabilitySettingOptions);
            // Add the row to the table
            _this.projectCapacitySettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.projectCapacitySettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsProjectOperationalChars = function () {
        var _this = this;
        // Set the setting table captions
        this.projectOperationalCharsSettingsTable = new SettingsTable();
        this.projectOperationalCharsSettingsTable.tableCaption =
            'Project operational characteristics';
        this.projectOperationalCharsSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingProjectOpChar()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectOperationalCharsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_operational_characteristics', 'projectOperationalCharsSetting', _this.projectOperationalCharsSettingOptions);
            // Add the row to the table
            _this.projectOperationalCharsSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.projectOperationalCharsSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsFuels = function () {
        var _this = this;
        // Set the setting table captions
        this.fuelSettingsTable = new SettingsTable();
        this.fuelSettingsTable.tableCaption = 'Fuels settings';
        this.fuelSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingFuels()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.fuelSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('fuel_characteristics', 'projectFuelsSetting', _this.fuelSettingOptions);
            // Add the row to the table
            _this.fuelSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingFuelPrices()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.fuelPricesSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('fuel_prices', 'fuelPricesSetting', _this.fuelPricesSettingOptions);
            // Add the row to the table
            _this.fuelSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.fuelSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsTransmissionCapacity = function () {
        var _this = this;
        // Set the setting table captions
        this.transmissionCapacitySettingsTable = new SettingsTable();
        this.transmissionCapacitySettingsTable.tableCaption =
            'Transmission capacity';
        this.transmissionCapacitySettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingTransmissionPortfolio()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.transmissionPortfolioSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('transmission_portfolio', 'transmissionPortfolioSetting', _this.transmissionPortfolioSettingOptions);
            // Add the row to the table
            _this.transmissionCapacitySettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingTransmissionExistingCapacity()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.transmissionExistingCapacitySettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('transmission_existing_capacity', 'transmissionExistingCapacitySetting', _this.transmissionExistingCapacitySettingOptions);
            // Add the row to the table
            _this.transmissionCapacitySettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.transmissionCapacitySettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsTransmissionOperationalChars = function () {
        var _this = this;
        // Set the setting table captions
        this.transmissionOperationalCharsSettingsTable = new SettingsTable();
        this.transmissionOperationalCharsSettingsTable.tableCaption =
            'Transmission operational characteristics';
        this.transmissionOperationalCharsSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingTransmissionOpChar()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.transmissionOperationalCharsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('transmission_operational_characteristics', 'transmissionOperationalCharsSetting', _this.transmissionOperationalCharsSettingOptions);
            // Add the row to the table
            _this.transmissionOperationalCharsSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.transmissionOperationalCharsSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsTransmissionHurdleRates = function () {
        var _this = this;
        // Set the setting table captions
        this.transmissionHurdleRatesSettingsTable = new SettingsTable();
        this.transmissionHurdleRatesSettingsTable.tableCaption =
            'Transmission hurdle rates';
        this.transmissionHurdleRatesSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingTransmissionHurdleRates()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.transmissionHurdleRatesSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('transmission_hurdle_rates', 'transmissionHurdleRatesSetting', _this.transmissionHurdleRatesSettingOptions);
            // Add the row to the table
            _this.transmissionHurdleRatesSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.transmissionHurdleRatesSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsTransmissionSimultaneousFlowLimits = function () {
        var _this = this;
        // Set the setting table captions
        this.transmissionSimultaneousFlowLimitsSettingsTable = new SettingsTable();
        this.transmissionSimultaneousFlowLimitsSettingsTable.tableCaption =
            'Transmission simultaneous flow limits';
        this.transmissionSimultaneousFlowLimitsSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingTransmissionSimFlowLimits()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.transmissionSimultaneousFlowLimitsSettingOptions =
                scenarioSetting;
            // Create the row
            var newRow = createRow('transmission_simultaneous_flow_limits', 'transmissionSimultaneousFlowLimitsSetting', _this.transmissionSimultaneousFlowLimitsSettingOptions);
            // Add the row to the table
            _this.transmissionSimultaneousFlowLimitsSettingsTable.settingRows
                .push(newRow);
        });
        this.scenarioNewService.getSettingTransmissionSimFlowLimitGroups()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.transmissionSimultaneousFlowLimitLineGroupsSettingOptions =
                scenarioSetting;
            // Create the row
            var newRow = createRow('transmission_simultaneous_flow_limit_line_groups', 'transmissionSimultaneousFlowLimitLineGroupsSetting', _this.transmissionSimultaneousFlowLimitLineGroupsSettingOptions);
            // Add the row to the table
            _this.transmissionSimultaneousFlowLimitsSettingsTable.settingRows
                .push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.transmissionSimultaneousFlowLimitsSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsLFReservesUp = function () {
        var _this = this;
        // Set the setting table captions
        this.loadFollowingUpSettingsTable = new SettingsTable();
        this.loadFollowingUpSettingsTable.tableCaption = 'Load following up settings';
        this.loadFollowingUpSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingLFReservesUpBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyLoadFollowingUpBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('geography_load_following_up_bas', 'geographyLoadFollowingUpBAsSetting', _this.geographyLoadFollowingUpBAsSettingOptions);
            // Add the row to the table
            _this.loadFollowingUpSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectLFReservesUpBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectLoadFollowingUpBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_load_following_up_bas', 'projectLoadFollowingUpBAsSetting', _this.projectLoadFollowingUpBAsSettingOptions);
            // Add the row to the table
            _this.loadFollowingUpSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingLFReservesUpRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.loadFollowingUpRequirementSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('load_following_up_requirement', 'loadFollowingUpRequirementSetting', _this.loadFollowingUpRequirementSettingOptions);
            // Add the row to the table
            _this.loadFollowingUpSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.loadFollowingUpSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsLFReservesDown = function () {
        var _this = this;
        // Set the setting table captions
        this.loadFollowingDownSettingsTable = new SettingsTable();
        this.loadFollowingDownSettingsTable.tableCaption = 'Load following down settings';
        this.loadFollowingDownSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingLFReservesDownBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyLoadFollowingDownBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('geography_load_following_down_bas', 'geographyLoadFollowingDownBAsSetting', _this.geographyLoadFollowingDownBAsSettingOptions);
            // Add the row to the table
            _this.loadFollowingDownSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectLFReservesDownBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectLoadFollowingDownBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_load_following_down_bas', 'projectLoadFollowingDownBAsSetting', _this.projectLoadFollowingDownBAsSettingOptions);
            // Add the row to the table
            _this.loadFollowingDownSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingLFReservesDownRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.loadFollowingDownRequirementSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('load_following_down_requirement', 'loadFollowingDownRequirementSetting', _this.loadFollowingDownRequirementSettingOptions);
            // Add the row to the table
            _this.loadFollowingDownSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.loadFollowingDownSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsRegulationUp = function () {
        var _this = this;
        // Set the setting table captions
        this.regulationUpSettingsTable = new SettingsTable();
        this.regulationUpSettingsTable.tableCaption = 'Regulation up settings';
        this.regulationUpSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingRegulationUpBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyRegulationUpBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('geography_regulation_up_bas', 'geographyRegulationUpBAsSetting', _this.geographyRegulationUpBAsSettingOptions);
            // Add the row to the table
            _this.regulationUpSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectRegulationUpBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectRegulationUpBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_regulation_up_bas', 'projectRegulationUpBAsSetting', _this.projectRegulationUpBAsSettingOptions);
            // Add the row to the table
            _this.regulationUpSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingRegulationUpRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.regulationUpRequirementSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('regulation_up_requirement', 'regulationUpRequirementSetting', _this.regulationUpRequirementSettingOptions);
            // Add the row to the table
            _this.regulationUpSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.regulationUpSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsRegulationDown = function () {
        var _this = this;
        // Set the setting table captions
        this.regulationDownSettingsTable = new SettingsTable();
        this.regulationDownSettingsTable.tableCaption = 'Regulation down settings';
        this.regulationDownSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingRegulationDownBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyRegulationDownBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('geography_regulation_down_bas', 'geographyRegulationDownBAsSetting', _this.geographyRegulationDownBAsSettingOptions);
            // Add the row to the table
            _this.regulationDownSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectRegulationDownBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectRegulationDownBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_regulation_down_bas', 'projectRegulationDownBAsSetting', _this.projectRegulationDownBAsSettingOptions);
            // Add the row to the table
            _this.regulationDownSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingRegulationDownRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.regulationDownRequirementSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('regulation_down_requirement', 'regulationDownRequirementSetting', _this.regulationDownRequirementSettingOptions);
            // Add the row to the table
            _this.regulationDownSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.regulationDownSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsSpinningReserves = function () {
        var _this = this;
        // Set the setting table captions
        this.spinningReservesSettingsTable = new SettingsTable();
        this.spinningReservesSettingsTable.tableCaption = '' +
            'Spinning reserves settings';
        this.spinningReservesSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingSpinningReservesBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographySpinningReservesBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('geography_spinning_reserves_bas', 'geographySpinningReservesBAsSetting', _this.geographySpinningReservesBAsSettingOptions);
            // Add the row to the table
            _this.spinningReservesSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectSpinningReservesBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectSpinningReservesBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_spinning_reserves_bas', 'projectSpinningReservesBAsSetting', _this.projectSpinningReservesBAsSettingOptions);
            // Add the row to the table
            _this.spinningReservesSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingSpinningReservesRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.spinningReservesRequirementSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('spinning_reserves_requirement', 'spinningReservesRequirementSetting', _this.spinningReservesRequirementSettingOptions);
            // Add the row to the table
            _this.spinningReservesSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.spinningReservesSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsFrequencyResponse = function () {
        var _this = this;
        // Set the setting table captions
        this.frequencyResponseSettingsTable = new SettingsTable();
        this.frequencyResponseSettingsTable.tableCaption =
            'Frequency response settings';
        this.frequencyResponseSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingFrequencyResponseBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyFrequencyResponseBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('geography_frequency_response_bas', 'geographyFrequencyResponseBAsSetting', _this.geographyFrequencyResponseBAsSettingOptions);
            // Add the row to the table
            _this.frequencyResponseSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectFrequencyResponseBAs()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectFrequencyResponseBAsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_frequency_response_bas', 'projectFrequencyResponseBAsSetting', _this.projectFrequencyResponseBAsSettingOptions);
            // Add the row to the table
            _this.frequencyResponseSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingFrequencyResponseRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.frequencyResponseRequirementSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('frequency_response_requirement', 'frequencyResponseRequirementSetting', _this.frequencyResponseRequirementSettingOptions);
            // Add the row to the table
            _this.frequencyResponseSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.frequencyResponseSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsRPS = function () {
        var _this = this;
        // Set the setting table captions
        this.rpsSettingsTable = new SettingsTable();
        this.rpsSettingsTable.tableCaption =
            'RPS settings';
        this.rpsSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingRPSAreas()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyRPSAreasSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('rps_areas', 'geographyRPSAreasSetting', _this.geographyRPSAreasSettingOptions);
            // Add the row to the table
            _this.rpsSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectRPSAreas()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectRPSAreasSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_rps_areas', 'projectRPSAreasSetting', _this.projectRPSAreasSettingOptions);
            // Add the row to the table
            _this.rpsSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingRPSRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.rpsTargetSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('rps_target', 'rpsTargetSetting', _this.rpsTargetSettingOptions);
            // Add the row to the table
            _this.rpsSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.rpsSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsCarbonCap = function () {
        var _this = this;
        // Set the setting table captions
        this.carbonCapSettingsTable = new SettingsTable();
        this.carbonCapSettingsTable.tableCaption =
            'CarbonCap settings';
        this.carbonCapSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingCarbonCapAreas()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyCarbonCapAreasSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('carbon_cap_areas', 'geographyCarbonCapAreasSetting', _this.geographyCarbonCapAreasSettingOptions);
            // Add the row to the table
            _this.carbonCapSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectCarbonCapAreas()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectCarbonCapAreasSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_carbon_cap_areas', 'projectCarbonCapAreasSetting', _this.projectCarbonCapAreasSettingOptions);
            // Add the row to the table
            _this.carbonCapSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingTransmissionCarbonCapAreas()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.transmissionCarbonCapAreasSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('transmission_carbon_cap_areas', 'transmissionCarbonCapAreasSetting', _this.transmissionCarbonCapAreasSettingOptions);
            // Add the row to the table
            _this.carbonCapSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingCarbonCapRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.carbonCapTargetSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('carbon_cap_target', 'carbonCapTargetSetting', _this.carbonCapTargetSettingOptions);
            // Add the row to the table
            _this.carbonCapSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.carbonCapSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsPRM = function () {
        var _this = this;
        // Set the setting table captions
        this.prmSettingsTable = new SettingsTable();
        this.prmSettingsTable.tableCaption =
            'PRM settings';
        this.prmSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingPRMAreas()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyPRMAreasSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('prm_areas', 'geographyPRMAreasSetting', _this.geographyPRMAreasSettingOptions);
            // Add the row to the table
            _this.prmSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectPRMAreas()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectPRMAreasSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_prm_areas', 'projectPRMAreasSetting', _this.projectPRMAreasSettingOptions);
            // Add the row to the table
            _this.prmSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingPRMRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.prmRequirementSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('prm_requirement', 'prmRequirementSetting', _this.prmRequirementSettingOptions);
            // Add the row to the table
            _this.prmSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingELCCSurface()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.elccSurfaceSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('elcc_surface', 'elccSurfaceSetting', _this.elccSurfaceSettingOptions);
            // Add the row to the table
            _this.prmSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectELCCChars()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectELCCCharsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_elcc_chars', 'projectELCCCharsSetting', _this.projectELCCCharsSettingOptions);
            // Add the row to the table
            _this.prmSettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectEnergyOnly()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectPRMEnergyOnlySettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_energy_only', 'projectPRMEnergyOnlySetting', _this.projectPRMEnergyOnlySettingOptions);
            // Add the row to the table
            _this.prmSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.prmSettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsLocalCapacity = function () {
        var _this = this;
        // Set the setting table captions
        this.localCapacitySettingsTable = new SettingsTable();
        this.localCapacitySettingsTable.tableCaption =
            'Local capacity settings';
        this.localCapacitySettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingLocalCapacityAreas()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.geographyLocalCapacityAreasSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('local_capacity_areas', 'geographyLocalCapacityAreasSetting', _this.geographyLocalCapacityAreasSettingOptions);
            // Add the row to the table
            _this.localCapacitySettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectLocalCapacityAreas()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectLocalCapacityAreasSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_local_capacity_areas', 'projectLocalCapacityAreasSetting', _this.projectLocalCapacityAreasSettingOptions);
            // Add the row to the table
            _this.localCapacitySettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingLocalCapacityRequirement()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.localCapacityRequirementSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('local_capacity_requirement', 'localCapacityRequirementSetting', _this.localCapacityRequirementSettingOptions);
            // Add the row to the table
            _this.localCapacitySettingsTable.settingRows.push(newRow);
        });
        this.scenarioNewService.getSettingProjectLocalCapacityChars()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.projectLocalCapacityCharsSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('project_local_capacity_chars', 'projectLocalCapacityCharsSetting', _this.projectLocalCapacityCharsSettingOptions);
            // Add the row to the table
            _this.localCapacitySettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.localCapacitySettingsTable);
    };
    ScenarioNewComponent.prototype.getSettingOptionsTuning = function () {
        var _this = this;
        // Set the setting table captions
        this.tuningSettingsTable = new SettingsTable();
        this.tuningSettingsTable.tableCaption = 'Tuning settings';
        this.tuningSettingsTable.settingRows = [];
        // Get the settings
        this.scenarioNewService.getSettingTuning()
            .subscribe(function (scenarioSetting) {
            // Get the settings from the server
            _this.tuningSettingOptions = scenarioSetting;
            // Create the row
            var newRow = createRow('tuning', 'tuningSetting', _this.tuningSettingOptions);
            // Add the row to the table
            _this.tuningSettingsTable.settingRows.push(newRow);
        });
        // Add the table to the scenario structure
        this.ScenarioNewStructure.push(this.tuningSettingsTable);
    };
    ScenarioNewComponent.prototype.saveNewScenario = function () {
        var socket = io.connect('http://127.0.0.1:8080/');
        socket.on('connect', function () {
            console.log("Connection established: " + socket.connected);
        });
        socket.emit('add_new_scenario', this.newScenarioForm.value);
    };
    ScenarioNewComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
            selector: 'app-scenario-new',
            template: __webpack_require__(/*! ./scenario-new.component.html */ "./src/app/scenario-new/scenario-new.component.html"),
            styles: [__webpack_require__(/*! ./scenario-new.component.css */ "./src/app/scenario-new/scenario-new.component.css")]
        }),
        tslib__WEBPACK_IMPORTED_MODULE_0__["__metadata"]("design:paramtypes", [_scenario_new_service__WEBPACK_IMPORTED_MODULE_3__["ScenarioNewService"]])
    ], ScenarioNewComponent);
    return ScenarioNewComponent;
}());

var Feature = /** @class */ (function () {
    function Feature() {
    }
    return Feature;
}());
var SettingsTable = /** @class */ (function () {
    function SettingsTable() {
    }
    return SettingsTable;
}());
var SettingRow = /** @class */ (function () {
    function SettingRow() {
    }
    return SettingRow;
}());
function featureSelectionOptions() {
    return ['', 'yes', 'no'];
}
function createRow(rowName, rowFormControlName, settingOptions) {
    var settingRow = new SettingRow();
    settingRow.rowName = rowName;
    settingRow.rowFormControlName = rowFormControlName;
    settingRow.settingOptions = settingOptions;
    return settingRow;
}


/***/ }),

/***/ "./src/app/scenario-new/scenario-new.service.ts":
/*!******************************************************!*\
  !*** ./src/app/scenario-new/scenario-new.service.ts ***!
  \******************************************************/
/*! exports provided: ScenarioNewService, Setting */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScenarioNewService", function() { return ScenarioNewService; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Setting", function() { return Setting; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");



var ScenarioNewService = /** @class */ (function () {
    function ScenarioNewService(http) {
        this.http = http;
        this.scenarioSettingsBaseURL = 'http://127.0.0.1:8080/scenario-settings';
    }
    ScenarioNewService.prototype.getSettingTemporal = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/temporal");
    };
    ScenarioNewService.prototype.getSettingLoadZones = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/load-zones");
    };
    ScenarioNewService.prototype.getSettingProjectLoadZones = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-load-zones");
    };
    ScenarioNewService.prototype.getSettingTransmissionLoadZones = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/tx-load-zones");
    };
    ScenarioNewService.prototype.getSettingSystemLoad = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/system-load");
    };
    ScenarioNewService.prototype.getSettingProjectPortfolio = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-portfolio");
    };
    ScenarioNewService.prototype.getSettingProjectExistingCapacity = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-existing-capacity");
    };
    ScenarioNewService.prototype.getSettingProjectExistingFixedCost = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-existing-fixed-cost");
    };
    ScenarioNewService.prototype.getSettingProjectNewCost = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-new-cost");
    };
    ScenarioNewService.prototype.getSettingProjectNewPotential = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-new-potential");
    };
    ScenarioNewService.prototype.getSettingProjectAvailability = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-availability");
    };
    ScenarioNewService.prototype.getSettingProjectOpChar = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-opchar");
    };
    ScenarioNewService.prototype.getSettingFuels = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/fuels");
    };
    ScenarioNewService.prototype.getSettingFuelPrices = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/fuel-prices");
    };
    ScenarioNewService.prototype.getSettingTransmissionPortfolio = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/transmission-portfolio");
    };
    ScenarioNewService.prototype.getSettingTransmissionExistingCapacity = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/transmission-existing-capacity");
    };
    ScenarioNewService.prototype.getSettingTransmissionOpChar = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/transmission-opchar");
    };
    ScenarioNewService.prototype.getSettingTransmissionHurdleRates = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/transmission-hurdle-rates");
    };
    ScenarioNewService.prototype.getSettingTransmissionSimFlowLimits = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/transmission-simflow-limits");
    };
    ScenarioNewService.prototype.getSettingTransmissionSimFlowLimitGroups = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/transmission-simflow-limit-groups");
    };
    ScenarioNewService.prototype.getSettingLFReservesUpBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/lf-reserves-up-bas");
    };
    ScenarioNewService.prototype.getSettingProjectLFReservesUpBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-lf-reserves-up-bas");
    };
    ScenarioNewService.prototype.getSettingLFReservesUpRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/lf-reserves-up-req");
    };
    ScenarioNewService.prototype.getSettingLFReservesDownBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/lf-reserves-down-bas");
    };
    ScenarioNewService.prototype.getSettingProjectLFReservesDownBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-lf-reserves-down-bas");
    };
    ScenarioNewService.prototype.getSettingLFReservesDownRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/lf-reserves-down-req");
    };
    ScenarioNewService.prototype.getSettingRegulationUpBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/regulation-up-bas");
    };
    ScenarioNewService.prototype.getSettingProjectRegulationUpBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-regulation-up-bas");
    };
    ScenarioNewService.prototype.getSettingRegulationUpRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/regulation-up-req");
    };
    ScenarioNewService.prototype.getSettingRegulationDownBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/regulation-down-bas");
    };
    ScenarioNewService.prototype.getSettingProjectRegulationDownBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-regulation-down-bas");
    };
    ScenarioNewService.prototype.getSettingRegulationDownRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/regulation-down-req");
    };
    ScenarioNewService.prototype.getSettingSpinningReservesBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/spin-bas");
    };
    ScenarioNewService.prototype.getSettingProjectSpinningReservesBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-spin-bas");
    };
    ScenarioNewService.prototype.getSettingSpinningReservesRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/spin-req");
    };
    ScenarioNewService.prototype.getSettingFrequencyResponseBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/freq-resp-bas");
    };
    ScenarioNewService.prototype.getSettingProjectFrequencyResponseBAs = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-freq-resp-bas");
    };
    ScenarioNewService.prototype.getSettingFrequencyResponseRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/freq-resp-req");
    };
    ScenarioNewService.prototype.getSettingRPSAreas = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/rps-areas");
    };
    ScenarioNewService.prototype.getSettingProjectRPSAreas = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-rps-areas");
    };
    ScenarioNewService.prototype.getSettingRPSRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/rps-req");
    };
    ScenarioNewService.prototype.getSettingCarbonCapAreas = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/carbon-cap-areas");
    };
    ScenarioNewService.prototype.getSettingProjectCarbonCapAreas = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-carbon-cap-areas");
    };
    ScenarioNewService.prototype.getSettingTransmissionCarbonCapAreas = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/transmission-carbon-cap-areas");
    };
    ScenarioNewService.prototype.getSettingCarbonCapRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/carbon-cap-req");
    };
    ScenarioNewService.prototype.getSettingPRMAreas = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/prm-areas");
    };
    ScenarioNewService.prototype.getSettingProjectPRMAreas = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-prm-areas");
    };
    ScenarioNewService.prototype.getSettingPRMRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/prm-req");
    };
    ScenarioNewService.prototype.getSettingELCCSurface = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/elcc-surface");
    };
    ScenarioNewService.prototype.getSettingProjectELCCChars = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-elcc-chars");
    };
    ScenarioNewService.prototype.getSettingProjectEnergyOnly = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-energy-only");
    };
    ScenarioNewService.prototype.getSettingLocalCapacityAreas = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/local-capacity-areas");
    };
    ScenarioNewService.prototype.getSettingProjectLocalCapacityAreas = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-local-capacity-areas");
    };
    ScenarioNewService.prototype.getSettingLocalCapacityRequirement = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/local-capacity-req");
    };
    ScenarioNewService.prototype.getSettingProjectLocalCapacityChars = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/project-local-capacity-chars");
    };
    ScenarioNewService.prototype.getSettingTuning = function () {
        return this.http.get(this.scenarioSettingsBaseURL + "/tuning");
    };
    ScenarioNewService = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Injectable"])({
            providedIn: 'root'
        }),
        tslib__WEBPACK_IMPORTED_MODULE_0__["__metadata"]("design:paramtypes", [_angular_common_http__WEBPACK_IMPORTED_MODULE_2__["HttpClient"]])
    ], ScenarioNewService);
    return ScenarioNewService;
}());

var Setting = /** @class */ (function () {
    function Setting() {
    }
    return Setting;
}());



/***/ }),

/***/ "./src/app/scenarios/scenarios.component.css":
/*!***************************************************!*\
  !*** ./src/app/scenarios/scenarios.component.css ***!
  \***************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "/* scenariosComponent's private CSS styles */\n.selected {\n  background-color: #CFD8DC !important;\n  color: white;\n}\n.scenarios {\n  margin: 0 0 2em 0;\n  list-style-type: none;\n  padding: 0;\n  width: 30em;\n}\n.scenarios li {\n  cursor: pointer;\n  position: relative;\n  left: 0;\n  background-color: #EEE;\n  margin: .5em;\n  padding: .3em 0;\n  height: 1.6em;\n  border-radius: 4px;\n}\n.scenarios li.selected:hover {\n  background-color: #BBD8DC !important;\n  color: white;\n}\n.scenarios li:hover {\n  color: #607D8B;\n  background-color: #DDD;\n  left: .1em;\n}\n.scenarios .text {\n  position: relative;\n  top: -3px;\n}\n.scenarios .badge {\n  display: inline-block;\n  font-size: small;\n  color: white;\n  padding: 0.8em 0.7em 0 0.7em;\n  background-color: #607D8B;\n  line-height: 1em;\n  position: relative;\n  left: -1px;\n  top: -4px;\n  height: 1.8em;\n  margin-right: .8em;\n  border-radius: 4px 0 0 4px;\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvc2NlbmFyaW9zL3NjZW5hcmlvcy5jb21wb25lbnQuY3NzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBLDRDQUE0QztBQUM1QztFQUNFLG9DQUFvQztFQUNwQyxZQUFZO0FBQ2Q7QUFDQTtFQUNFLGlCQUFpQjtFQUNqQixxQkFBcUI7RUFDckIsVUFBVTtFQUNWLFdBQVc7QUFDYjtBQUNBO0VBQ0UsZUFBZTtFQUNmLGtCQUFrQjtFQUNsQixPQUFPO0VBQ1Asc0JBQXNCO0VBQ3RCLFlBQVk7RUFDWixlQUFlO0VBQ2YsYUFBYTtFQUNiLGtCQUFrQjtBQUNwQjtBQUNBO0VBQ0Usb0NBQW9DO0VBQ3BDLFlBQVk7QUFDZDtBQUNBO0VBQ0UsY0FBYztFQUNkLHNCQUFzQjtFQUN0QixVQUFVO0FBQ1o7QUFDQTtFQUNFLGtCQUFrQjtFQUNsQixTQUFTO0FBQ1g7QUFDQTtFQUNFLHFCQUFxQjtFQUNyQixnQkFBZ0I7RUFDaEIsWUFBWTtFQUNaLDRCQUE0QjtFQUM1Qix5QkFBeUI7RUFDekIsZ0JBQWdCO0VBQ2hCLGtCQUFrQjtFQUNsQixVQUFVO0VBQ1YsU0FBUztFQUNULGFBQWE7RUFDYixrQkFBa0I7RUFDbEIsMEJBQTBCO0FBQzVCIiwiZmlsZSI6InNyYy9hcHAvc2NlbmFyaW9zL3NjZW5hcmlvcy5jb21wb25lbnQuY3NzIiwic291cmNlc0NvbnRlbnQiOlsiLyogc2NlbmFyaW9zQ29tcG9uZW50J3MgcHJpdmF0ZSBDU1Mgc3R5bGVzICovXG4uc2VsZWN0ZWQge1xuICBiYWNrZ3JvdW5kLWNvbG9yOiAjQ0ZEOERDICFpbXBvcnRhbnQ7XG4gIGNvbG9yOiB3aGl0ZTtcbn1cbi5zY2VuYXJpb3Mge1xuICBtYXJnaW46IDAgMCAyZW0gMDtcbiAgbGlzdC1zdHlsZS10eXBlOiBub25lO1xuICBwYWRkaW5nOiAwO1xuICB3aWR0aDogMzBlbTtcbn1cbi5zY2VuYXJpb3MgbGkge1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIHBvc2l0aW9uOiByZWxhdGl2ZTtcbiAgbGVmdDogMDtcbiAgYmFja2dyb3VuZC1jb2xvcjogI0VFRTtcbiAgbWFyZ2luOiAuNWVtO1xuICBwYWRkaW5nOiAuM2VtIDA7XG4gIGhlaWdodDogMS42ZW07XG4gIGJvcmRlci1yYWRpdXM6IDRweDtcbn1cbi5zY2VuYXJpb3MgbGkuc2VsZWN0ZWQ6aG92ZXIge1xuICBiYWNrZ3JvdW5kLWNvbG9yOiAjQkJEOERDICFpbXBvcnRhbnQ7XG4gIGNvbG9yOiB3aGl0ZTtcbn1cbi5zY2VuYXJpb3MgbGk6aG92ZXIge1xuICBjb2xvcjogIzYwN0Q4QjtcbiAgYmFja2dyb3VuZC1jb2xvcjogI0RERDtcbiAgbGVmdDogLjFlbTtcbn1cbi5zY2VuYXJpb3MgLnRleHQge1xuICBwb3NpdGlvbjogcmVsYXRpdmU7XG4gIHRvcDogLTNweDtcbn1cbi5zY2VuYXJpb3MgLmJhZGdlIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xuICBmb250LXNpemU6IHNtYWxsO1xuICBjb2xvcjogd2hpdGU7XG4gIHBhZGRpbmc6IDAuOGVtIDAuN2VtIDAgMC43ZW07XG4gIGJhY2tncm91bmQtY29sb3I6ICM2MDdEOEI7XG4gIGxpbmUtaGVpZ2h0OiAxZW07XG4gIHBvc2l0aW9uOiByZWxhdGl2ZTtcbiAgbGVmdDogLTFweDtcbiAgdG9wOiAtNHB4O1xuICBoZWlnaHQ6IDEuOGVtO1xuICBtYXJnaW4tcmlnaHQ6IC44ZW07XG4gIGJvcmRlci1yYWRpdXM6IDRweCAwIDAgNHB4O1xufVxuIl19 */"

/***/ }),

/***/ "./src/app/scenarios/scenarios.component.html":
/*!****************************************************!*\
  !*** ./src/app/scenarios/scenarios.component.html ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<h2>My Scenarios</h2>\n<button ng-click=\"updateScenarios\" class=\"button-primary\"\n        (click)=\"updateScenarios()\">Update scenarios list</button>\n<ul class=\"scenarios\">\n  <li *ngFor=\"let scenario of scenarios\"\n    [class.selected]=\"scenario.id === selectedId\">\n    <a [routerLink]=\"['/scenario', scenario.id]\">\n      <span class=\"badge\">{{ scenario.id }}</span>{{ scenario.name }}\n    </a>\n  </li>\n</ul>\n<button ng-click=\"newScenario\" class=\"button-primary\">\n        <a [routerLink]=\"['/scenario-new']\">New scenario</a>\n</button>\n"

/***/ }),

/***/ "./src/app/scenarios/scenarios.component.ts":
/*!**************************************************!*\
  !*** ./src/app/scenarios/scenarios.component.ts ***!
  \**************************************************/
/*! exports provided: ScenariosComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScenariosComponent", function() { return ScenariosComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _scenarios_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./scenarios.service */ "./src/app/scenarios/scenarios.service.ts");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");




var ScenariosComponent = /** @class */ (function () {
    function ScenariosComponent(scenariosService, route) {
        this.scenariosService = scenariosService;
        this.route = route;
        console.log("Constructing scenarios...");
    }
    ScenariosComponent.prototype.ngOnInit = function () {
        console.log("Initializing scenarios...");
        this.getScenarios();
    };
    // onSelect(scenario: Scenario): void {
    //   this.selectedScenario = scenario;
    // }
    ScenariosComponent.prototype.getScenarios = function () {
        var _this = this;
        console.log("Getting scenarios...");
        this.scenariosService.getScenarios()
            .subscribe(function (scenarios) { return _this.scenarios = scenarios; });
    };
    ScenariosComponent.prototype.updateScenarios = function (event) {
        console.log('Updating scenarios...');
        this.getScenarios();
    };
    ScenariosComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
            selector: 'app-scenarios',
            template: __webpack_require__(/*! ./scenarios.component.html */ "./src/app/scenarios/scenarios.component.html"),
            styles: [__webpack_require__(/*! ./scenarios.component.css */ "./src/app/scenarios/scenarios.component.css")]
        }),
        tslib__WEBPACK_IMPORTED_MODULE_0__["__metadata"]("design:paramtypes", [_scenarios_service__WEBPACK_IMPORTED_MODULE_2__["ScenariosService"],
            _angular_router__WEBPACK_IMPORTED_MODULE_3__["ActivatedRoute"]])
    ], ScenariosComponent);
    return ScenariosComponent;
}());



/***/ }),

/***/ "./src/app/scenarios/scenarios.service.ts":
/*!************************************************!*\
  !*** ./src/app/scenarios/scenarios.service.ts ***!
  \************************************************/
/*! exports provided: ScenariosService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScenariosService", function() { return ScenariosService; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");



var ScenariosService = /** @class */ (function () {
    function ScenariosService(http) {
        this.http = http;
        this.scenariosURL = 'http://127.0.0.1:8080/scenarios/';
    }
    ScenariosService.prototype.getScenarios = function () {
        console.log(this.http.get(this.scenariosURL));
        return this.http.get(this.scenariosURL);
    };
    ScenariosService = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Injectable"])({
            providedIn: 'root'
        }),
        tslib__WEBPACK_IMPORTED_MODULE_0__["__metadata"]("design:paramtypes", [_angular_common_http__WEBPACK_IMPORTED_MODULE_2__["HttpClient"]])
    ], ScenariosService);
    return ScenariosService;
}());



/***/ }),

/***/ "./src/app/settings/settings.component.css":
/*!*************************************************!*\
  !*** ./src/app/settings/settings.component.css ***!
  \*************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IiIsImZpbGUiOiJzcmMvYXBwL3NldHRpbmdzL3NldHRpbmdzLmNvbXBvbmVudC5jc3MifQ== */"

/***/ }),

/***/ "./src/app/settings/settings.component.html":
/*!**************************************************!*\
  !*** ./src/app/settings/settings.component.html ***!
  \**************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<h2>Settings</h2>\n<div>\n    <input class=\"u-full-width\" size=\"50\" placeholder=\"GridPath folder\"\n  type=\"text\"\n           [(ngModel)]=\"gridPathFolder\">\n    <button id=\"browseGPFolder\" class=\"button-primary\"\n            (click)=\"browseGPFolder()\">Browse</button>\n</div>\n<div><span>Current GridPath folder setting: </span>{{currentGridPathFolderSetting}}</div>\n<div>\n    <input class=\"u-full-width\" size=\"50\" placeholder=\"GridPath database\"\n           type=\"text\"\n           [(ngModel)]=\"gridPathDB\">\n    <button id=\"browseGPDatabase\" class=\"button-primary\"\n            (click)=\"browseGPDatabase()\">Browse</button>\n</div>\n<div><span>Current GridPath database setting: </span>{{currentGridPathDatabaseSetting}}</div>\n<div>\n    <input class=\"u-full-width\" size=\"50\" placeholder=\"Python binary\"\n           type=\"text\"\n           [(ngModel)]=\"pythonBinary\">\n    <button id=\"browsePythonBinary\" class=\"button-primary\"\n            (click)=\"browsePythonBinary()\">Browse</button>\n</div>\n<div><span>Current Python binary setting: </span>{{currentPythonBinarySetting}}</div>\n"

/***/ }),

/***/ "./src/app/settings/settings.component.ts":
/*!************************************************!*\
  !*** ./src/app/settings/settings.component.ts ***!
  \************************************************/
/*! exports provided: SettingsComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SettingsComponent", function() { return SettingsComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");


var electron = window.require('electron');
var SettingsComponent = /** @class */ (function () {
    function SettingsComponent(zone) {
        var _this = this;
        this.zone = zone;
        console.log("Constructing the settings...");
        // Get current settings from Electron
        this.requestStoredSettings();
        electron.ipcRenderer.on('sendStoredSettings', function (event, data) {
            console.log('Got stored settings from Electron main');
            console.log(data);
            zone.run(function () {
                // Handle situation if no value is set
                if (data['gridPathDirectory']['value'] === null) {
                    _this.currentGridPathFolderSetting = null;
                }
                else {
                    _this.currentGridPathFolderSetting =
                        data['gridPathDirectory']['value'][0];
                }
                if (data['gridPathDatabase']['value'] === null) {
                    _this.currentGridPathDatabaseSetting = null;
                }
                else {
                    _this.currentGridPathDatabaseSetting =
                        data['gridPathDatabase']['value'][0];
                }
                if (data['pythonBinary']['value'] === null) {
                    _this.currentPythonBinarySetting = null;
                }
                else {
                    _this.currentPythonBinarySetting =
                        data['pythonBinary']['value'][0];
                }
            });
        });
        // TODO: treatment is very similar for different settings, so could be
        //  re-factored
        // When a setting button is clicked by sending, a message is first sent
        // to the Electron main, which then communicates back to the renderer
        // on the channels included in the 'constructor' method, so that we can
        // set the paths inside the Angular zone (which can happen in
        // the 'constructor' method only)
        // Set GridPath folder setting via Electron dialog
        electron.ipcRenderer.on('onClickGridPathFolderSettingAngular', function (event) {
            electron.remote.dialog.showOpenDialog({ title: 'Select a the GridPath folder', properties: ['openDirectory'] }, function (folderPath) {
                if (folderPath === undefined) {
                    console.log("No folder selected");
                    return;
                }
                // We must run this inside the Angular zone to get Angular to
                // detect the change and update the view immediately
                else {
                    // Send Electron the new value
                    console.log("Sending GridPath folder setting to Electron");
                    electron.ipcRenderer.send("setGridPathFolderSetting", folderPath);
                    // Ask Electron for the value it stored (double-check value is
                    // the same as what we just selected)
                    _this.requestStoredSettings();
                    // Electron responds on this channel
                    electron.ipcRenderer.on('sendStoredSettings', function (event, data) {
                        console.log('Got stored settings from Electron main');
                        console.log(data);
                        // Set the new value for currentGridPathFolderSetting in Angular
                        zone.run(function () {
                            if (data['gridPathDirectory']['value'] === null) {
                                _this.currentGridPathFolderSetting = null;
                            }
                            else {
                                _this.currentGridPathFolderSetting =
                                    data['gridPathDirectory']['value'][0];
                            }
                            console.log("Setting current GP folder to " + _this.currentGridPathFolderSetting + " in Angular");
                            // Also update the selection box with what we just selected
                            // This provides a visual confirmation that Angular and
                            // Electron are seeing the same value
                            // TODO: write a check that the two values are the same
                            _this.gridPathFolder = folderPath;
                        });
                    });
                }
                console.log("GridPath folder set to " + _this.gridPathFolder);
            });
        });
        // Set GridPath database setting via Electron dialog
        electron.ipcRenderer.on('onClickGridPathDatabaseSettingAngular', function (event) {
            electron.remote.dialog.showOpenDialog({ title: 'Select a the GridPath database file',
                properties: ['openFile'] }, function (dbFilePath) {
                if (dbFilePath === undefined) {
                    console.log("No file selected");
                    return;
                }
                // We must run this inside the Angular zone to get Angular to
                // detect the change and update the view immediately
                else {
                    // Send Electron the new value
                    console.log("Sending GridPath database setting to Electron");
                    electron.ipcRenderer.send("setGridPathDatabaseSetting", dbFilePath);
                    // Ask Electron for the value it stored (double-check value is
                    // the same as what we just selected)
                    _this.requestStoredSettings();
                    // Electron responds on this channel
                    electron.ipcRenderer.on('sendStoredSettings', function (event, data) {
                        console.log('Got stored settings from Electron main');
                        console.log(data);
                        // Set the new value for currentGridPathDatabaseSetting in Angular
                        zone.run(function () {
                            if (data['gridPathDatabase']['value'] === null) {
                                _this.currentGridPathDatabaseSetting = null;
                            }
                            else {
                                _this.currentGridPathDatabaseSetting =
                                    data['gridPathDatabase']['value'][0];
                            }
                            console.log("Setting current GP database to " + _this.currentGridPathDatabaseSetting + " in Angular");
                            // Also update the selection box with what we just selected
                            // This provides a visual confirmation that Angular and
                            // Electron are seeing the same value
                            // TODO: write a check that the two values are the same
                            _this.gridPathDB = dbFilePath;
                        });
                    });
                }
                console.log("GridPath database set to " + _this.gridPathDB[0]);
            });
        });
        // Set Python binary directory setting via Electron dialog
        electron.ipcRenderer.on('onClickPythonBinarySettingAngular', function (event) {
            electron.remote.dialog.showOpenDialog({ title: 'Select a the Python binary file',
                properties: ['openDirectory'] }, function (pythonBinaryPath) {
                if (pythonBinaryPath === undefined) {
                    console.log("No file selected");
                    return;
                }
                // We must run this inside the Angular zone to get Angular to
                // detect the change and update the view immediately
                else {
                    // Send Electron the new value
                    console.log("Sending Python binary directory setting to" +
                        " Electron");
                    electron.ipcRenderer.send("setPythonBinarySetting", pythonBinaryPath);
                    // Ask Electron for the value it stored (double-check value is
                    // the same as what we just selected)
                    _this.requestStoredSettings();
                    // Electron responds on this channel
                    electron.ipcRenderer.on('sendStoredSettings', function (event, data) {
                        console.log('Got stored settings from Electron main');
                        console.log(data);
                        // Set the new value for currentPythonBinarySetting in Angular
                        zone.run(function () {
                            if (data['pythonBinary']['value'] === null) {
                                _this.currentPythonBinarySetting = null;
                            }
                            else {
                                _this.currentPythonBinarySetting =
                                    data['pythonBinary']['value'][0];
                            }
                            console.log("Setting current Python binary directory to " + _this.currentPythonBinarySetting + " in Angular");
                            // Also update the selection box with what we just selected
                            // This provides a visual confirmation that Angular and
                            // Electron are seeing the same value
                            // TODO: write a check that the two values are the same
                            _this.pythonBinary = pythonBinaryPath;
                        });
                    });
                }
                console.log("Python binary set to " + _this.pythonBinary[0]);
            });
        });
    }
    SettingsComponent.prototype.browseGPFolder = function (event) {
        console.log("Request to set GP folder setting...");
        electron.ipcRenderer.send('onClickGridPathFolderSetting');
    };
    SettingsComponent.prototype.browseGPDatabase = function (event, zone) {
        console.log("Request to set GP database setting...");
        electron.ipcRenderer.send('onClickGridPathDatabaseSetting');
    };
    SettingsComponent.prototype.browsePythonBinary = function (event, zone) {
        console.log("Request to set Python binary setting...");
        electron.ipcRenderer.send('onClickPythonBinarySetting');
    };
    SettingsComponent.prototype.ngOnInit = function () {
        console.log("Initializing settings...");
    };
    SettingsComponent.prototype.requestStoredSettings = function () {
        console.log('Requesting stored settings from Electron main...');
        electron.ipcRenderer.send('requestStoredSettings');
    };
    SettingsComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
            selector: 'app-settings',
            template: __webpack_require__(/*! ./settings.component.html */ "./src/app/settings/settings.component.html"),
            styles: [__webpack_require__(/*! ./settings.component.css */ "./src/app/settings/settings.component.css")]
        }),
        tslib__WEBPACK_IMPORTED_MODULE_0__["__metadata"]("design:paramtypes", [_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgZone"]])
    ], SettingsComponent);
    return SettingsComponent;
}());



/***/ }),

/***/ "./src/environments/environment.ts":
/*!*****************************************!*\
  !*** ./src/environments/environment.ts ***!
  \*****************************************/
/*! exports provided: environment */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "environment", function() { return environment; });
// This file can be replaced during build by using the `fileReplacements` array.
// `ng build --prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.
var environment = {
    production: false
};
/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.


/***/ }),

/***/ "./src/main.ts":
/*!*********************!*\
  !*** ./src/main.ts ***!
  \*********************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/platform-browser-dynamic */ "./node_modules/@angular/platform-browser-dynamic/fesm5/platform-browser-dynamic.js");
/* harmony import */ var _app_app_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./app/app.module */ "./src/app/app.module.ts");
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./environments/environment */ "./src/environments/environment.ts");




if (_environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].production) {
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["enableProdMode"])();
}
Object(_angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__["platformBrowserDynamic"])().bootstrapModule(_app_app_module__WEBPACK_IMPORTED_MODULE_2__["AppModule"])
    .catch(function (err) { return console.error(err); });


/***/ }),

/***/ 0:
/*!***************************!*\
  !*** multi ./src/main.ts ***!
  \***************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(/*! /Users/ana/dev/gridpath-ui-dev/ui-angular-cli738/src/main.ts */"./src/main.ts");


/***/ })

},[[0,"runtime","vendor"]]]);
//# sourceMappingURL=main.js.map