var SearchBox = React.createClass({ 
    render: function() {
        return (
            <div>
                <span>{this.props.name}:</span><input type="text" />
            </div>
        )
    }
});

module.exports = SearchBox;