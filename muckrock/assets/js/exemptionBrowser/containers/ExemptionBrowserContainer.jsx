/* ExemptionBrowserContainer.jsx
**
** Connects the ExemptionBrowser to the store.
*/

import { connect } from 'react-redux';

import ExemptionBrowser from '../components/ExemptionBrowser';
import {
    displayExemptionDetail,
    displayExemptionList,
    displayExemptionForm,
} from '../actions';

const mapStateToProps = (store) => ({
    activeExemption: store.exemptions.exemption,
    formIsVisible: store.exemptions.formIsVisible,
});

const mapDispatchToProps = (dispatch) => ({
    displayExemptionList: () => {
        dispatch(displayExemptionList());
    },
});

const ExemptionBrowserContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionBrowser)

export default ExemptionBrowserContainer
