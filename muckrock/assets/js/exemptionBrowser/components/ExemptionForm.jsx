/* ExemptionForm.jsx
**
** The exemption form allows a user to request help with an exemption.
** They should fill in the language the agency used to invoke and identify the exemption.
*/

import React, { PropTypes } from 'react';
import { Field, reduxForm } from 'redux-form';

const ExemptionForm = ({onCancel, onSubmit, handleSubmit}) => {
    const handleCancel = (e) => {
        e.preventDefault();
        onCancel();
    }
    return (
        <form className="exemption__form form panel" method="post" onSubmit={handleSubmit}>
            <h2>Submit a new exemption</h2>
            <div className="field">
                <label htmlFor="languageInput">What language did the agency use to invoke the exemption?</label>
                <Field name="languageInput" component="textarea" />
            </div>
            <footer>
                <span onClick={handleCancel} className="button">Cancel</span>
                <button type="submit" className="blue button">Submit</button>
            </footer>
        </form>
    )
};

export default reduxForm({
    form: 'exemptionSubmit'
})(ExemptionForm);
