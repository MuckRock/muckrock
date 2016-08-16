/* ExemptionBrowser.jsx
**
** This is the root component for the Exemption Browser feature.
** It should provide a search field, a listing of search results, and the ability to
** see the details of a specific result.
*/

import React, { PropTypes } from 'react';

import ExemptionSearch from './ExemptionSearch';
import ExemptionList from './ExemptionList';
import ExemptionDetail from './ExemptionDetail';

const ExemptionBrowser = ({exemptionQuery, exemptionResults, activeExemption, onQueryChange, searchExemptions, displayExemptionDetail, displayExemptionList}) => {
    let resultDisplay;
    if (!activeExemption) {
        resultDisplay = <ExemptionList exemptions={exemptionResults} onExemptionClick={displayExemptionDetail} />;
    } else {
        resultDisplay = <ExemptionDetail exemption={activeExemption} onBackClick={displayExemptionList} />;
    }
    return (
        <div className="exemptionBrowser">
            <ExemptionSearch query={exemptionQuery} onSubmit={searchExemptions} />
            {resultDisplay}
        </div>
    )
};

ExemptionBrowser.propTypes = {
    exemptionQuery: PropTypes.string.isRequired,
    exemptionResults: PropTypes.array.isRequired,
    activeExemption: PropTypes.object,
    searchExemptions: PropTypes.func.isRequired,
    displayExemptionDetail: PropTypes.func.isRequired,
    displayExemptionList: PropTypes.func.isRequired,
};

export default ExemptionBrowser
