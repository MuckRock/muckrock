import { createStore } from 'redux';
import { initialState, dashboardReducer } from './reducer';

const devTool = window.devToolsExtension ? window.devToolsExtension() : undefined;
const store = createStore(dashboardReducer, initialState, devTool);
export default store;
