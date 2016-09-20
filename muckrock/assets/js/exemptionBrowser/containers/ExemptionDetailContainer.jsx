/* ExemptionDetailContainer.jsx
**
** Connects the ExemptionDetail component to the store and actions.
*/

import { connect } from 'react-redux';

import ExemptionDetail from '../components/ExemptionDetail';
import { updateVisibilityFilter } from '../actions';

const mapStateToProps = (store) => ({
    exemption: store.exemptions.exemption
});

const mapDispatchToProps = (dispatch) => ({
    onBackClick: () => {
        dispatch(updateVisibilityFilter('SHOW_SEARCH'));
    },
});

const ExemptionDetailContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionDetail);

export default ExemptionDetailContainer;
