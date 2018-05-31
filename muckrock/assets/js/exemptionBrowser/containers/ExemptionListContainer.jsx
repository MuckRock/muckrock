/* ExemptionListContainer.jsx
**
** Connects the ExemptionList component to the state and actions.
*/

import { connect } from 'react-redux';

import ExemptionList from '../components/ExemptionList';
import { selectExemption, updateVisibilityFilter } from '../actions';

const mapStateToProps = (store) => ({
    loading: store.exemptions.loading,
    query: store.exemptions.query,
    exemptions: store.exemptions.results,
});

const mapDispatchToProps = (dispatch) => ({
    showExemptionDetail: (exemption) => {
        dispatch(selectExemption(exemption));
        dispatch(updateVisibilityFilter('SHOW_DETAIL'));
    },
    showExemptionForm: () => {
        /* eslint-disable no-undef */
        mixpanel.track('Get Appeal Help');
        /* eslint-enable no-undef */
        dispatch(updateVisibilityFilter('SHOW_FORM'));
    },
});

const ExemptionListContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionList);

export default ExemptionListContainer;
