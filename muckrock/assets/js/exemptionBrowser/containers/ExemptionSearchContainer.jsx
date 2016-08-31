/* ExemptionSearchContainer.jsx
**
** Connects the exemption state and actions to the search component.
*/

import { connect } from 'react-redux';

import ExemptionSearch from '../components/ExemptionSearch';
import {
    searchExemptions,
    resetExemptionState,
} from '../actions';

// Get initial values for the search form
// Right now we need to pull them from the DOM,
// since we're only layering this React appliaction.
const jurisdictionId = $('#dom-data').data('jurisdiction');

const mapStateToProps = (store) => ({
    initialValues: {
        'q': store.exemptions.query,
        'jurisdiction': jurisdictionId
    }
});

const mapDispatchToProps = (dispatch) => ({
    onSubmit: (data) => {
        const q = data.q;
        if (q === undefined || q == '') {
            dispatch(resetExemptionState());
        } else {
            dispatch(searchExemptions(data));
        }
    },
});

const ExemptionSearchContainer = connect(mapStateToProps, mapDispatchToProps)(ExemptionSearch);

export default ExemptionSearchContainer;
