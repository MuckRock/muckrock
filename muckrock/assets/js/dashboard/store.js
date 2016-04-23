import { createStore } from 'redux';
import dashboardReducer from './reducer';

const store = createStore(dashboardReducer);
export default store;
