/* ExemptionSearchInput.jsx
**
** This is a component that renders an input form for searching exemptions.
** When it is submitted, the form will trigger an action for making a query
** to the exemption search API.
*/

import React from 'react';
import { Field, reduxForm } from 'redux-form';

const ExemptionSearch = ({handleSubmit}) => {
    // handleSubmit is provided by reduxForm, and it calls
    // onSubmit with the data from the form fields
    return (
        <form method="get"
              className="nomargin"
              onSubmit={handleSubmit}>
            <label htmlFor="q" className="bold">Search for exemptions and appeals</label>
            <div className="exemption-search">
                <Field name="q" component="input" type="search" />
                <Field name="jurisdiction" component="input" type="hidden" />
                <button type="submit" className="basic blue button">Search</button>
            </div>
        </form>
    );
};

export default reduxForm({
    form: 'exemptionSearch'
})(ExemptionSearch);
