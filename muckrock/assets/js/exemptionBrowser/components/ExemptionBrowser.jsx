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
import ExemptionForm from './ExemptionForm';

const ExemptionBrowser = ({exemptionQuery, exemptionResults, activeExemption, formIsVisible, loadingResults, onQueryChange, searchExemptions, displayExemptionDetail, displayExemptionList, displayExemptionForm}) => {
    let resultDisplay;
    if (formIsVisible) {
        resultDisplay = <ExemptionForm onCancel={displayExemptionList} onSubmit={()=>{alert('Handle submit!')}}/>;
    } else if (activeExemption) {
        resultDisplay = <ExemptionDetail exemption={activeExemption} onBackClick={displayExemptionList} />;
    } else {
        resultDisplay = (
            <div>
                <ExemptionSearch query={exemptionQuery} onSubmit={searchExemptions} />
                <ExemptionList query={exemptionQuery} exemptions={exemptionResults} loading={loadingResults} onExemptionClick={displayExemptionDetail}
                displayExemptionForm={displayExemptionForm} />
            </div>
        );
    }
    return (
        <div className="exemptionBrowser">
            {resultDisplay}
        </div>
    )
};

ExemptionBrowser.propTypes = {
    exemptionQuery: PropTypes.string.isRequired,
    exemptionResults: PropTypes.array.isRequired,
    activeExemption: PropTypes.object,
    formIsVisible: PropTypes.bool.isRequired,
    loadingResults: PropTypes.bool.isRequired,
    searchExemptions: PropTypes.func.isRequired,
    displayExemptionDetail: PropTypes.func.isRequired,
    displayExemptionList: PropTypes.func.isRequired,
    displayExemptionForm: PropTypes.func.isRequired,
};

export default ExemptionBrowser
