/* ExemptionFormContainer.jsx
**
** Connects form component to store and actions.
*/

import axios from 'axios';
import { connect } from 'react-redux';

import ExemptionForm from '../components/ExemptionForm';
import { updateVisibilityFilter } from '../actions';

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
        console.debug('Handle submit');
        axios.post('exemptions/submit', {
            data: data,
            xsrfCookieName: 'csrftoken',
            xsrfHeaderName: 'X-CSRFToken',
        }).then(response => {
            console.debug('Posted successfully:', response);
        }).catch(error => {
            console.debug('Posted unsuccessfully:', error);
        })
        alert('Handle submit!');
    }
});

const ExemptionFormContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionForm);

export default ExemptionFormContainer;
