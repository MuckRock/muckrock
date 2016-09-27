/* ExemptionList.jsx
**
** Renders a list of exemptions.
*/

import React, { PropTypes } from 'react';

import Loader from './Loader';

function truncateString(string, maxLength) {
    if (string.length > maxLength) {
        string = string.substring(0, maxLength) + '...';
    }
    return string
}

const ExemptionListItem = ({exemption, onClick}) => {
    const basisMaxLength = 300;
    const truncatedBasis = truncateString(exemption.basis, basisMaxLength);
    const handleClick = (e) => {
        e.preventDefault();
        onClick(exemption);
    }
    return (
        <li className="exemption__list__item textbox nomargin" onClick={handleClick}>
            <p className="exemption__name bold">{exemption.name} &rarr;</p>
            <p className="exemption__basis">{truncatedBasis}</p>
            <p className="link">See More</p>
        </li>
    )
};

const ExemptionList = ({query, loading, exemptions, showExemptionDetail, showExemptionForm}) => {
    const exemptionListItems = exemptions.map((exemption, i) => (
        <ExemptionListItem key={i} exemption={exemption} onClick={showExemptionDetail} />
    ));
    let emptyResults = null;
    let renderedList = null;
    if (query !== null) {
        if (exemptions.length > 0) {
            emptyResults = (
                <div className="exemption__empty small">
                    <p className="bold nomargin">Are these results unhelpful?</p>
                    <p className="nomargin">Tell us how your request was rejected and we'll help you appeal it.</p>
                    <button onClick={showExemptionForm} className="button">Submit Information</button>
                </div>
            )
            renderedList = (
                <div className="exemption__results">
                    <ul className="exemption__list nostyle nomargin">
                        {exemptionListItems}
                    </ul>
                    {emptyResults}
                </div>
            )
        } else if (loading) {
            renderedList = (
                <div className="exemption__results--loading">
                    <Loader />
                </div>
            )
        } else {
            emptyResults = (
                <div className="exemption__empty">
                    <p className="bold nomargin">We don't have anything in our database yet for "{query}".</p>
                    <p>Tell us how your request was rejected and we'll help you appeal it.</p>
                    <button onClick={showExemptionForm} className="button">Submit Information</button>
                </div>
            )
            renderedList = (
                <div className="exemption__results">
                    {emptyResults}
                </div>
            )
        }
    }
    return renderedList
};

ExemptionList.propTypes = {
    query: PropTypes.string,
    loading: PropTypes.bool.isRequired,
    exemptions: PropTypes.array.isRequired,
    showExemptionDetail: PropTypes.func.isRequired,
    showExemptionForm: PropTypes.func.isRequired,
}

export default ExemptionList
