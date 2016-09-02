/* ExemptionFormContainer.jsx
**
** Connects form component to store and actions.
*/

import axios from 'axios';
import { connect } from 'react-redux';

import ExemptionForm from '../components/ExemptionForm';
import { updateVisibilityFilter, submitExemption } from '../actions';

// We get the FOIA ID from the DOM because this
// application cannot see the entire request page
const foiaID = $('#dom-data').data('request');

const mapStateToProps = (state) => ({
    initialValues: {
        foia: foiaID
    }
});

const mapDispatchToProps = (dispatch) => ({
    onCancel: () => {
        dispatch(updateVisibilityFilter('SHOW_SEARCH'));
    },
    onSubmit: (data) => {
        dispatch(submitExemption(data));
    }
});

const ExemptionFormContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionForm);

export default ExemptionFormContainer;
