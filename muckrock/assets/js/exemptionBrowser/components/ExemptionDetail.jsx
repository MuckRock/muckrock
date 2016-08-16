/* ExemptionDetail.jsx
**
** Renders details about a single exemption.
*/

import React, { PropTypes } from 'react';

const AppealLanguage = ({appeal}) => {
    const handleClick = (e) => {
        /*
        We're gonna cheat here and break out of the React context. When handling the appeal button click, we're going to append the appeal language to the appeal composer box.

        Hopefully we'll migrate most of the composer over to React/Redux also! But until that happens, we'll just use jQuery to pop it in.
        */
        const language = appeal.language;
        const $appealComposer = $('#appeal-composer');
        $appealComposer.val($appealComposer.val() + '\n\n' + language);
    }
    return (
        <div className="exemption__detail__appeal">
            <p>{appeal.context}</p>
            <textarea readOnly value={appeal.language}></textarea>
            <p className="small">Use this language in your appeal</p>
            <button className="button" onClick={handleClick}>Sample</button>
        </div>
    )
};

const ExemptionDetail = ({exemption, onBackClick}) => {
    const appeals = exemption.example_appeals.map((appeal, i) => (
        <AppealLanguage key={i} appeal={appeal} />
    ));
    return (
        <div className="exemption__detail">
            <p onClick={onBackClick}>&larr; Back to results</p>
            <h1>{exemption.name}</h1>
            <p>{exemption.basis}</p>
            <h2>Sample Apppeals</h2>
            {appeals}
        </div>
    )
};

ExemptionDetail.propTypes = {
    exemption: PropTypes.object.isRequired,
    onBackClick: PropTypes.func.isRequired,
}

export default ExemptionDetail
