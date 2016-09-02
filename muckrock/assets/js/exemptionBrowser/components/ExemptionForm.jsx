/* ExemptionForm.jsx
**
** The exemption form allows a user to request help with an exemption.
** They should fill in the language the agency used to invoke and identify the exemption.
*/

import React, { PropTypes } from 'react';
import { Field, reduxForm } from 'redux-form';

import Loader from './Loader';
import {SuccessIcon, FailureIcon} from './Icons';

const ExemptionForm = ({currentState, response, onDismiss, onCancel, handleSubmit}) => {
    const handleDismiss = (e) => {
        e.preventDefault();
        onDismiss();
    }
    const handleCancel = (e) => {
        e.preventDefault();
        onCancel();
    }
    let ajaxFilter;
    switch (currentState) {
        case 'LOADING':
            ajaxFilter = (
                <div className="loading overlay">
                    <Loader />
                </div>
            )
            break;
        case 'SUCCESS':
            ajaxFilter = (
                <div className="success overlay">
                    <div>
                        <SuccessIcon />
                        <p className="bold">Success!</p>
                        <p>MuckRock staff will get back to you soon!</p>
                        <button className="button" onClick={handleCancel}>Go Back</button>
                    </div>
                </div>
            )
            break;
        case 'FAILURE':
            ajaxFilter = (
                <div className="failure overlay">
                    <div>
                        <FailureIcon />
                        <p className="bold">An error occurred</p>
                        <p>We're sorry! Try again?</p>
                        <button className="button" onClick={handleDismiss}>Dismiss</button>
                    </div>
                </div>
            )
            break;
        default:
            ajaxFilter = null;
    }
    return (
        <form className="exemption__form form panel overlay__container" method="post" onSubmit={handleSubmit}>
            {ajaxFilter}
            <h2>Submit a new exemption</h2>
            <div className="field">
                <label htmlFor="language">What language did the agency use to invoke the exemption?</label>
                <Field name="language" component="textarea" />
                <Field name="foia" component="input" type="hidden" />
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
