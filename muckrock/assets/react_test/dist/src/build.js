(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({"/Users/jeff/Documents/muckrock/muckrock/muckrock/assets/react_test/src/js/App.js":[function(require,module,exports){
var SearchContainer = require('./SearchContainer'); 

React.render(React.createElement(SearchContainer, null), document.getElementById('react-test'));  

},{"./SearchContainer":"/Users/jeff/Documents/muckrock/muckrock/muckrock/assets/react_test/src/js/SearchContainer.js"}],"/Users/jeff/Documents/muckrock/muckrock/muckrock/assets/react_test/src/js/SearchBox.js":[function(require,module,exports){
var SearchBox = React.createClass({displayName: "SearchBox", 
    render: function() {
        return (
            React.createElement("div", null, 
                React.createElement("span", null, this.props.name, ":"), React.createElement("input", {type: "text"})
            )
        )
    }
});

module.exports = SearchBox;

},{}],"/Users/jeff/Documents/muckrock/muckrock/muckrock/assets/react_test/src/js/SearchContainer.js":[function(require,module,exports){
var SearchBox = require('./SearchBox');

var SearchContainer = React.createClass({displayName: "SearchContainer", 
    render: function() {
    	var divStyle = {
    		border: 'solid 1px black',
    		display: 'inline-block',
			padding: '5px'
    	};
        return (
            React.createElement("div", {style: divStyle}, 
                React.createElement(SearchBox, {name: "search"})
            )
        )
    }
});
module.exports = SearchContainer;

},{"./SearchBox":"/Users/jeff/Documents/muckrock/muckrock/muckrock/assets/react_test/src/js/SearchBox.js"}]},{},["/Users/jeff/Documents/muckrock/muckrock/muckrock/assets/react_test/src/js/App.js"])
//# sourceMappingURL=data:application/json;charset:utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm5vZGVfbW9kdWxlcy9icm93c2VyaWZ5L25vZGVfbW9kdWxlcy9icm93c2VyLXBhY2svX3ByZWx1ZGUuanMiLCIvVXNlcnMvamVmZi9Eb2N1bWVudHMvbXVja3JvY2svbXVja3JvY2svbXVja3JvY2svYXNzZXRzL3JlYWN0X3Rlc3Qvc3JjL2pzL0FwcC5qcyIsIi9Vc2Vycy9qZWZmL0RvY3VtZW50cy9tdWNrcm9jay9tdWNrcm9jay9tdWNrcm9jay9hc3NldHMvcmVhY3RfdGVzdC9zcmMvanMvU2VhcmNoQm94LmpzIiwiL1VzZXJzL2plZmYvRG9jdW1lbnRzL211Y2tyb2NrL211Y2tyb2NrL211Y2tyb2NrL2Fzc2V0cy9yZWFjdF90ZXN0L3NyYy9qcy9TZWFyY2hDb250YWluZXIuanMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7QUNBQSxJQUFJLGVBQWUsR0FBRyxPQUFPLENBQUMsbUJBQW1CLENBQUMsQ0FBQzs7QUFFbkQsS0FBSyxDQUFDLE1BQU0sQ0FBQyxvQkFBQyxlQUFlLEVBQUEsSUFBQSxDQUFHLENBQUEsRUFBRSxRQUFRLENBQUMsY0FBYyxDQUFDLFlBQVksQ0FBQyxDQUFDLENBQUM7OztBQ0Z6RSxJQUFJLCtCQUErQix5QkFBQTtJQUMvQixNQUFNLEVBQUUsV0FBVztRQUNmO1lBQ0ksb0JBQUEsS0FBSSxFQUFBLElBQUMsRUFBQTtnQkFDRCxvQkFBQSxNQUFLLEVBQUEsSUFBQyxFQUFDLElBQUksQ0FBQyxLQUFLLENBQUMsSUFBSSxFQUFDLEdBQVEsQ0FBQSxFQUFBLG9CQUFBLE9BQU0sRUFBQSxDQUFBLENBQUMsSUFBQSxFQUFJLENBQUMsTUFBTSxDQUFBLENBQUcsQ0FBQTtZQUNsRCxDQUFBO1NBQ1Q7S0FDSjtBQUNMLENBQUMsQ0FBQyxDQUFDOztBQUVILE1BQU0sQ0FBQyxPQUFPLEdBQUcsU0FBUzs7O0FDVjFCLElBQUksU0FBUyxHQUFHLE9BQU8sQ0FBQyxhQUFhLENBQUMsQ0FBQzs7QUFFdkMsSUFBSSxxQ0FBcUMsK0JBQUE7SUFDckMsTUFBTSxFQUFFLFdBQVc7S0FDbEIsSUFBSSxRQUFRLEdBQUc7TUFDZCxNQUFNLEVBQUUsaUJBQWlCO01BQ3pCLE9BQU8sRUFBRSxjQUFjO0dBQzFCLE9BQU8sRUFBRSxLQUFLO01BQ1gsQ0FBQztRQUNDO1lBQ0ksb0JBQUEsS0FBSSxFQUFBLENBQUEsQ0FBQyxLQUFBLEVBQUssQ0FBRSxRQUFVLENBQUEsRUFBQTtnQkFDbEIsb0JBQUMsU0FBUyxFQUFBLENBQUEsQ0FBQyxJQUFBLEVBQUksQ0FBQyxRQUFRLENBQUEsQ0FBRyxDQUFBO1lBQ3pCLENBQUE7U0FDVDtLQUNKO0NBQ0osQ0FBQyxDQUFDO0FBQ0gsTUFBTSxDQUFDLE9BQU8sR0FBRyxlQUFlIiwiZmlsZSI6ImdlbmVyYXRlZC5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzQ29udGVudCI6WyIoZnVuY3Rpb24gZSh0LG4scil7ZnVuY3Rpb24gcyhvLHUpe2lmKCFuW29dKXtpZighdFtvXSl7dmFyIGE9dHlwZW9mIHJlcXVpcmU9PVwiZnVuY3Rpb25cIiYmcmVxdWlyZTtpZighdSYmYSlyZXR1cm4gYShvLCEwKTtpZihpKXJldHVybiBpKG8sITApO3ZhciBmPW5ldyBFcnJvcihcIkNhbm5vdCBmaW5kIG1vZHVsZSAnXCIrbytcIidcIik7dGhyb3cgZi5jb2RlPVwiTU9EVUxFX05PVF9GT1VORFwiLGZ9dmFyIGw9bltvXT17ZXhwb3J0czp7fX07dFtvXVswXS5jYWxsKGwuZXhwb3J0cyxmdW5jdGlvbihlKXt2YXIgbj10W29dWzFdW2VdO3JldHVybiBzKG4/bjplKX0sbCxsLmV4cG9ydHMsZSx0LG4scil9cmV0dXJuIG5bb10uZXhwb3J0c312YXIgaT10eXBlb2YgcmVxdWlyZT09XCJmdW5jdGlvblwiJiZyZXF1aXJlO2Zvcih2YXIgbz0wO288ci5sZW5ndGg7bysrKXMocltvXSk7cmV0dXJuIHN9KSIsInZhciBTZWFyY2hDb250YWluZXIgPSByZXF1aXJlKCcuL1NlYXJjaENvbnRhaW5lcicpOyBcblxuUmVhY3QucmVuZGVyKDxTZWFyY2hDb250YWluZXIgLz4sIGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdyZWFjdC10ZXN0JykpOyAgIiwidmFyIFNlYXJjaEJveCA9IFJlYWN0LmNyZWF0ZUNsYXNzKHsgXG4gICAgcmVuZGVyOiBmdW5jdGlvbigpIHtcbiAgICAgICAgcmV0dXJuIChcbiAgICAgICAgICAgIDxkaXY+XG4gICAgICAgICAgICAgICAgPHNwYW4+e3RoaXMucHJvcHMubmFtZX06PC9zcGFuPjxpbnB1dCB0eXBlPVwidGV4dFwiIC8+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgKVxuICAgIH1cbn0pO1xuXG5tb2R1bGUuZXhwb3J0cyA9IFNlYXJjaEJveDsiLCJ2YXIgU2VhcmNoQm94ID0gcmVxdWlyZSgnLi9TZWFyY2hCb3gnKTtcblxudmFyIFNlYXJjaENvbnRhaW5lciA9IFJlYWN0LmNyZWF0ZUNsYXNzKHsgXG4gICAgcmVuZGVyOiBmdW5jdGlvbigpIHtcbiAgICBcdHZhciBkaXZTdHlsZSA9IHtcbiAgICBcdFx0Ym9yZGVyOiAnc29saWQgMXB4IGJsYWNrJyxcbiAgICBcdFx0ZGlzcGxheTogJ2lubGluZS1ibG9jaycsXG5cdFx0XHRwYWRkaW5nOiAnNXB4J1xuICAgIFx0fTtcbiAgICAgICAgcmV0dXJuIChcbiAgICAgICAgICAgIDxkaXYgc3R5bGU9e2RpdlN0eWxlfT5cbiAgICAgICAgICAgICAgICA8U2VhcmNoQm94IG5hbWU9XCJzZWFyY2hcIiAvPlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgIClcbiAgICB9XG59KTtcbm1vZHVsZS5leHBvcnRzID0gU2VhcmNoQ29udGFpbmVyOyJdfQ==
