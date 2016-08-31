/* ExemptionFormContainer.jsx
**
** Connects form component to store and actions.
*/

import axios from 'axios';
import { connect } from 'react-redux';

import ExemptionForm from '../components/ExemptionForm';
import { updateVisibilityFilter, submitExemption } from '../actions';

const requestId = $('#dom-data').data('request');

const mapStateToProps = (state) => ({
    initialValues: {
        request: requestId
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
