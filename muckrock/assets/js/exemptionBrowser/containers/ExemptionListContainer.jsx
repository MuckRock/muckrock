/* ExemptionListContainer.jsx
**
** Connects the ExemptionList component to the state and actions.
*/

import { connect } from 'react-redux';

import ExemptionList from '../components/ExemptionList';
import { displayExemptionDetail, displayExemptionForm } from '../actions';

const mapStateToProps = (store) => ({
    loading: store.exemptions.loading,
    query: store.exemptions.query,
    exemptions: store.exemptions.results,
});

const mapDispatchToProps = (dispatch) => ({
    showExemptionDetail: (exemption) => {
        dispatch(displayExemptionDetail(exemption));
    },
    showExemptionForm: () => {
        dispatch(displayExemptionForm());
    },
});

const ExemptionListContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionList);

export default ExemptionListContainer;
