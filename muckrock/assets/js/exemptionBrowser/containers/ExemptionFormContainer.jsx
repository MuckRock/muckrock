/* ExemptionFormContainer.jsx
**
** Connects form component to store and actions.
*/

import axios from 'axios';
import { connect } from 'react-redux';

import ExemptionForm from '../components/ExemptionForm';
import { updateVisibilityFilter, submitExemption, submitExemptionState } from '../actions';

// We get the FOIA ID from the DOM because this
// application cannot see the entire request page
const foiaID = $('#dom-data').data('request');

const mapStateToProps = (state) => ({
    initialValues: {
        foia: foiaID
    },
    currentState: state.exemptions.submission_form.state,
    response: state.exemptions.submission_form.response,
});

const mapDispatchToProps = (dispatch) => ({
    onDismiss: () => {
        dispatch(submitExemptionState('DEFAULT'));
    },
    onCancel: () => {
        dispatch(updateVisibilityFilter('SHOW_SEARCH'));
        dispatch(submitExemptionState('DEFAULT'));
    },
    onSubmit: (data) => {
        dispatch(submitExemption(data));
    }
});

const ExemptionFormContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionForm);

export default ExemptionFormContainer;
