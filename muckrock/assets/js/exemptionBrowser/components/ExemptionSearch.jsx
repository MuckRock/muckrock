/* ExemptionSearchInput.jsx
**
** This is a component that renders an input form for searching exemptions.
** When it is submitted, the form will trigger an action for making a query
** to the exemption search API.
*/

import React, { PropTypes } from 'react';

const ExemptionSearch = ({onSubmit, query}) => {
    let input;
    return (
        <form method="get"
              className="exemption-search"
              onSubmit={e => {
                  e.preventDefault();
                  onSubmit(input.value);
              }}>
            <input type="search" name="q" ref={node => { input = node }}/>
            <button type="submit" className="basic blue button">Search</button>
        </form>
    );
};

ExemptionSearch.propTypes = {
    onSubmit: PropTypes.func.isRequired,
    query: PropTypes.string.isRequired,
}

export default ExemptionSearch
