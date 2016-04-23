const initialState = {
    data: {}
}

const dashboardReducer = function(state = initialState, action) {
    switch(action.type) {
        case 'GET_DATA_SUCCESS':
            return Object.assign({}, state, { data: action.data });
    }
    return state;
}

export default dashboardReducer;
