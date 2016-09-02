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
        const id = appeal.id;
        const $appealForm = $('#appeal .composer-input');
        const $appealComposer = $appealForm.find('#appeal-composer');
        /*
        Insert the language into the textarea
        If there's nothing else in the textarea, don't pad it with spacing.
        But if there is, give a clean linebreak between whatever exists and
        What we're adding.
        */
        const currentValue = $appealComposer.val();
        let spacing = '\n\n';
        if (currentValue.length == 0) {
            spacing = '';
        }
        $appealComposer.val(currentValue + spacing + language);
        /*
        Insert the appeal id as a hidden value into the form.
        This way, we can track what appeal language is being
        used and how frequently.
        */
        const $appealInputElement = $('<input type="hidden" name="appeal_language" value="' + id + '"/>');
        $appealInputElement.insertAfter($appealComposer);
    }
    return (
        <div className="exemption__detail__appeal">
            <p>{appeal.context}</p>
            <div className="grid__row">
                <div className="grid__column three-quarters">
                    <textarea readOnly rows="3" value={appeal.language}></textarea>
                </div>
                <div className="grid__column quarter">
                    <p className="small nomargin">Use this language in your appeal.</p>
                    <button className="button" onClick={handleClick}>Sample</button>
                </div>
            </div>
        </div>
    )
};

const ExemptionDetail = ({exemption, onBackClick}) => {
    const appeals = exemption.example_appeals.map((appeal, i) => (
        <AppealLanguage key={i} appeal={appeal} />
    ));
    return (
        <div>
            <button className="basic button w100 exemption__backButton" onClick={onBackClick}>&larr; Back to search results</button>
            <div className="exemption__detail textbox nomargin">
                <h1>{exemption.name}</h1>
                <p>{exemption.basis}</p>
                <h2>Sample Appeals</h2>
                {appeals}
            </div>
            <button className="basic button w100 exemption__backButton" onClick={onBackClick}>&larr; Back to search results</button>
        </div>
    )
};

ExemptionDetail.propTypes = {
    exemption: PropTypes.object.isRequired,
    onBackClick: PropTypes.func.isRequired,
}

export default ExemptionDetail
