/* ExemptionDetail.jsx
**
** Renders details about a single exemption.
*/

import React, { PropTypes } from 'react';

const ExemptionDetail = ({exemption, onBackClick}) => (
    <div className="exemption__detail">
        <p onClick={onBackClick}>&larr; Back to results</p>
        <h1>{exemption.name}</h1>
        <p>{exemption.basis}</p>
    </div>
);

ExemptionDetail.propTypes = {
    exemption: PropTypes.object.isRequired,
    onBackClick: PropTypes.func.isRequired,
}

export default ExemptionDetail
