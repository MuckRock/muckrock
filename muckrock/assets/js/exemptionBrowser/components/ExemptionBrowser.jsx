/* ExemptionBrowser.jsx
**
** This is the root component for the Exemption Browser feature.
** It should provide a search field, a listing of search results, and the ability to
** see the details of a specific result.
*/

import React, { PropTypes } from 'react';

import ExemptionSearchContainer from '../containers/ExemptionSearchContainer';
import ExemptionListContainer from '../containers/ExemptionListContainer';
import ExemptionDetail from './ExemptionDetail';
import ExemptionForm from './ExemptionForm';

const ExemptionBrowser = ({filter, activeExemption, displayExemptionList}) => {
    let resultDisplay;
    if (filter == 'SHOW_SEARCH') {
        resultDisplay = (
            <div>
                <ExemptionSearchContainer />
                <ExemptionListContainer />
            </div>
        );
    } else if (filter == 'SHOW_DETAIL') {
        resultDisplay = <ExemptionDetail exemption={activeExemption} onBackClick={displayExemptionList} />;
    } else if (filter == 'SHOW_FORM') {
        resultDisplay = <ExemptionForm onCancel={displayExemptionList} onSubmit={()=>{alert('Handle submit!')}}/>;
    } else {
        resultDisplay = <ExemptionSearchContainer />
    }
    return (
        <div className="exemptionBrowser">
            {resultDisplay}
        </div>
    )
};

ExemptionBrowser.propTypes = {
    filter: PropTypes.string.isRequired,
    activeExemption: PropTypes.object,
    displayExemptionList: PropTypes.func.isRequired,
};

export default ExemptionBrowser
