/* ExemptionList.jsx
**
** Renders a list of exemptions.
*/

import React, { PropTypes } from 'react';

const ExemptionListItem = ({exemption, onClick}) => {
    const handleClick = (e) => {
        e.preventDefault();
        onClick(exemption);
    }
    return (
        <li className="exemption__list__item" onClick={handleClick}>
            <p className="exemption__name">{exemption.name} &rarr;</p>
        </li>
    )
};

const ExemptionList = ({query, exemptions, onExemptionClick}) => {
    const exemptionListItems = exemptions.map((exemption, i) => (
        <ExemptionListItem key={i} exemption={exemption} onClick={onExemptionClick} />
    ));
    let emptyResults = null;
    let renderedList = null;
    if (query != '') {
        if (exemptions.length > 0) {
            emptyResults = (
                <div className="exemption__empty">
                    <p>Can't find what you're looking for?</p>
                    <button onClick={e => { alert('Do something!')}} className="button">Submit Exemption</button>
                </div>
            )
            renderedList = (
                <div className="exemption__results">
                    <ul className="exemption__list">
                        {exemptionListItems}
                    </ul>
                    {emptyResults}
                </div>
            )
        } else {
            emptyResults = (
                <div className="exemption__empty">
                    <p>Sorry, we did not find any results for "{query}"</p>
                    <button onClick={e => { alert('Do something!')}} className="button">Submit Exemption</button>
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
    exemptions: PropTypes.array.isRequired,
    onExemptionClick: PropTypes.func.isRequired,
}

export default ExemptionList
