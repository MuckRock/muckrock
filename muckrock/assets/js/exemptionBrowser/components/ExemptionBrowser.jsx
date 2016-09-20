/* ExemptionBrowser.jsx
**
** This is the root component for the Exemption Browser feature.
** It should provide a search field, a listing of search results, and the ability to
** see the details of a specific result.
*/

import React, { PropTypes } from 'react';

import ExemptionSearchContainer from '../containers/ExemptionSearchContainer';
import ExemptionListContainer from '../containers/ExemptionListContainer';
import ExemptionDetailContainer from '../containers/ExemptionDetailContainer';
import ExemptionFormContainer from '../containers/ExemptionFormContainer';

const ExemptionSearchError = () => (
    <div className="exemption__empty">
        <p className="bold">An error occurred.</p>
        <p>We're very sorry! We've already been notified and are looking into it.</p>
    </div>
);

const ExemptionBrowser = ({filter}) => {
    let resultDisplay;
    if (filter == 'SHOW_SEARCH') {
        resultDisplay = (
            <div>
                <ExemptionSearchContainer />
                <ExemptionListContainer />
            </div>
        );
    } else if (filter == 'SHOW_DETAIL') {
        resultDisplay = <ExemptionDetailContainer />;
    } else if (filter == 'SHOW_FORM') {
        resultDisplay = <ExemptionFormContainer />;
    } else if (filter == 'SHOW_ERROR') {
        resultDisplay = (
            <div>
                <ExemptionSearchContainer />
                <ExemptionSearchError />
            </div>
        )
    } else {
        resultDisplay = <ExemptionSearchContainer />;
    }
    return (
        <div className="exemptionBrowser">
            {resultDisplay}
        </div>
    )
};

ExemptionBrowser.propTypes = {
    filter: PropTypes.string.isRequired
};

export default ExemptionBrowser
