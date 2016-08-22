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

const ExemptionBrowser = ({activeExemption, formIsVisible, displayExemptionList}) => {
    let resultDisplay;
    if (formIsVisible) {
        resultDisplay = <ExemptionForm onCancel={displayExemptionList} onSubmit={()=>{alert('Handle submit!')}}/>;
    } else if (activeExemption) {
        resultDisplay = <ExemptionDetail exemption={activeExemption} onBackClick={displayExemptionList} />;
    } else {
        resultDisplay = (
            <div>
                <ExemptionSearchContainer />
                <ExemptionListContainer />
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
    activeExemption: PropTypes.object,
    formIsVisible: PropTypes.bool.isRequired,
    displayExemptionList: PropTypes.func.isRequired,
};

export default ExemptionBrowser
