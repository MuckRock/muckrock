/* ExemptionList.jsx
**
** Renders a list of exemptions.
*/

import React, { PropTypes } from 'react';

function truncateString(string, maxLength) {
    if (string.length > maxLength) {
        string = string.substring(0, maxLength) + '...';
    }
    return string
}

const Loader = () => (
    <div className="loader">
        <div className="loader-inner line-scale-pulse-out-rapid">
            <div></div>
            <div></div>
            <div></div>
            <div></div>
            <div></div>
        </div>
    </div>
)

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
        </li>
    )
};

const ExemptionList = ({query, loading, exemptions, onExemptionClick, displayExemptionForm}) => {
    const exemptionListItems = exemptions.map((exemption, i) => (
        <ExemptionListItem key={i} exemption={exemption} onClick={onExemptionClick} />
    ));
    let emptyResults = null;
    let renderedList = null;
    if (query != '') {
        if (exemptions.length > 0) {
            emptyResults = (
                <div className="exemption__empty small">
                    <p className="bold nomargin">Are these results unhelpful?</p>
                    <p className="nomargin">Tell us more about your exemption and we'll help you appeal it.</p>
                    <button onClick={displayExemptionForm} className="button">Submit Exemption</button>
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
                    <p className="bold nomargin">We can't find anything related to "{query}"</p>
                    <p>Tell us more about your exemption and we'll help you appeal it.</p>
                    <button onClick={displayExemptionForm} className="button">Submit Exemption</button>
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
    query: PropTypes.string.isRequired,
    loading: PropTypes.bool.isRequired,
    exemptions: PropTypes.array.isRequired,
    onExemptionClick: PropTypes.func.isRequired,
    displayExemptionForm: PropTypes.func.isRequired,
}

export default ExemptionList
