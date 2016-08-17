/* ExemptionSearchInput.jsx
**
** This is a component that renders an input form for searching exemptions.
** When it is submitted, the form will trigger an action for making a query
** to the exemption search API.
*/

import React, { PropTypes } from 'react';

const ExemptionSearch = ({onSubmit, query}) => {
    let input;
    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.value != query) {
          onSubmit(input.value);
        }
    }
    return (
        <form method="get"
              className="nomargin"
              onSubmit={handleSubmit}>
            <label htmlFor="exemptionSearch" className="bold">Search for exemptions and appeals</label>
            <div className="exemption-search">
                <input type="search" name="q" id="exemptionSearch" ref={node => { input = node }}/>
                <button type="submit" className="basic blue button">Search</button>
            </div>
        </form>
    );
};

ExemptionSearch.propTypes = {
    onSubmit: PropTypes.func.isRequired,
    query: PropTypes.string.isRequired,
}

export default ExemptionSearch
