/* ExemptionList.jsx
**
** Renders a list of exemptions.
*/

import React, { PropTypes } from 'react';

const ExemptionListItem = ({exemption, onClick}) => {
    const handleClick = (e) => {
        e.preventDefault();
        console.log(exemption);
        onClick(exemption);
    }
    return (
        <li className="exemption__list__item" onClick={handleClick}>
            <p className="exemption__name">{exemption.name} &rarr;</p>
        </li>
    )
};

const ExemptionList = ({exemptions, onExemptionClick}) => {
    const exemptionListItems = exemptions.map((exemption, i) => (
        <ExemptionListItem key={i} exemption={exemption} onClick={onExemptionClick} />
    ));
    return (
        <ul className="exemption__list">
            {exemptionListItems}
        </ul>
    )
};

ExemptionList.propTypes = {
    exemptions: PropTypes.array.isRequired,
    onExemptionClick: PropTypes.func.isRequired,
}

export default ExemptionList
