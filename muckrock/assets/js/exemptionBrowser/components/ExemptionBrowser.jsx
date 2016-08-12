/* ExemptionBrowser.jsx
**
** This is the root component for the Exemption Browser feature.
** It should provide a search field, a listing of search results, and the ability to
** see the details of a specific result.
*/

import React, { PropTypes } from 'react';

const ExemptionBrowser = ({foo, onIncrementClick, onDecrementClick}) => (
    <div className="exemptionBrowser">
        <h1>Hello world!</h1>
        <p>Foo: {foo}</p>
        <button onClick={onIncrementClick}>Increment</button>
        <button onClick={onDecrementClick}>Decrement</button>
    </div>
);

ExemptionBrowser.propTypes = {
    foo: PropTypes.number.isRequired,
    onIncrementClick: PropTypes.func.isRequired,
    onDecrementClick: PropTypes.func.isRequired,
};

export default ExemptionBrowser
