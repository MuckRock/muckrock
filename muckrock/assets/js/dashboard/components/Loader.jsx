import React from 'react';

export const Loader = React.createClass({
    render: function() {
        return (
            <div className="loader">
                <div className="loader-inner line-scale-pulse-out-rapid">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
            </div>
        )
    }
});
