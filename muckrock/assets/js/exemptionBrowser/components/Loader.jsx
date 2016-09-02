/* Loader.jsx
**
** Renders a loading indicator. A small, but quite necessary, component.
*/

import React from 'react';

const Loader = () => (
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

export default Loader;
