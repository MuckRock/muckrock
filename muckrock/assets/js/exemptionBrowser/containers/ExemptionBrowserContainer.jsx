/* ExemptionBrowserContainer.jsx
**
** Connects the ExemptionBrowser to the store.
*/

import { connect } from 'react-redux';

import ExemptionBrowser from '../components/ExemptionBrowser';
import { updateVisibilityFilter } from '../actions';

const mapStateToProps = (store) => ({
    filter: store.exemptions.filter,
});

const ExemptionBrowserContainer = connect(mapStateToProps)(ExemptionBrowser);

export default ExemptionBrowserContainer
