/* ExemptionFormContainer.jsx
**
** Connects form component to store and actions.
*/

import { connect } from 'react-redux';

import ExemptionForm from '../components/ExemptionForm';
import { updateVisibilityFilter } from '../actions';

const mapStateToProps = (state) => ({

});

const mapDispatchToProps = (dispatch) => ({
    onCancel: () => {
        dispatch(updateVisibilityFilter('SHOW_SEARCH'));
    },
    onSubmit: () => {
        alert('Handle submit!');
    }
});

const ExemptionFormContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionForm);

export default ExemptionFormContainer;
