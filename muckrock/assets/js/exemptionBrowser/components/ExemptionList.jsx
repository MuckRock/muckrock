/* ExemptionList.jsx
**
** Renders a list of exemptions.
*/

import React, { PropTypes } from 'react';

const Exemption = ({id, name}) => (
    <div className="exemption" id={"exemption." + id}>
        <p className="exemption__name">
            {name}
        </p>
    </div>
);

const ExemptionListItem = ({exemption}) => (
    <li className="exemption__list__item">
        <Exemption id={exemption.id} name={exemption.name} />
    </li>
)

const ExemptionList = ({exemptions}) => {
    const exemptionListItems = exemptions.map((exemption, i) => (
        <ExemptionListItem key={i} exemption={exemption} />
    ));
    return (
        <ul className="exemption__list">
            {exemptionListItems}
        </ul>
    )
};

ExemptionList.propTypes = {
    exemptions: PropTypes.array.isRequired,
}

export default ExemptionList
