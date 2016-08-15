/* ExemptionSearchInput.jsx
**
** This is a component that renders an input form for searching exemptions.
** When it is submitted, the form will trigger an action for making a query
** to the exemption search API.
*/

import React, { PropTypes } from 'react';

const exemptionSearchAPI = '/api_v1/exemption/search/';

const ExemptionSearch = ({onSubmit, query}) => (
    <form method="get" action={exemptionSearchAPI} className="exemption-search" onSubmit={onSubmit}>
        <input type="search" name="q" value={query} />
        <button type="submit" className="basic blue button">Search</button>
    </form>
);

ExemptionBrowser.propTypes = {
    onSubmit: PropTypes.func.isRequired,
    query: PropTypes.string,
}

export default ExemptionSearch
