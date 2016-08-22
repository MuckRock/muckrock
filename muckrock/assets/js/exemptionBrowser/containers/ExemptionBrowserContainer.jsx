/* ExemptionBrowserContainer.jsx
**
** Connects the ExemptionBrowser to the store.
*/

import { connect } from 'react-redux';

import ExemptionBrowser from '../components/ExemptionBrowser';
import { updateVisibilityFilter } from '../actions';

const mapStateToProps = (store) => ({
    filter: store.exemptions.filter,
    activeExemption: store.exemptions.exemption,
});

const mapDispatchToProps = (dispatch) => ({
    displayExemptionList: () => {
        dispatch(updateVisibilityFilter('SHOW_SEARCH'));
    },
});

const ExemptionBrowserContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionBrowser)

export default ExemptionBrowserContainer
