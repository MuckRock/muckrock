function daysBefore(days, date) {
    var newDate = new Date(date.getTime());
    newDate.setDate(date.getDate() - days);
    return newDate;
}

var today = new Date(2016, 2, 1);
var yesterday = daysBefore(1, today);

export const initialState = {
    loading: false,
    error: null,
    data: [],
    dates: {
        'min': daysBefore(7, yesterday),
        'max': yesterday
    }
}

export const dashboardReducer = function(state = initialState, action) {
    switch(action.type) {
        case 'GET_DATA_LOADING':
            return Object.assign({}, state, {
                loading: true
            });
        case 'GET_DATA_SUCCESS':
            return Object.assign({}, state, {
                loading: false,
                data: action.response.data,
            });
        case 'GET_DATA_ERROR':
            return Object.assign({}, state, {
                loading: false,
                error: action.error,
            });
    }
    return state;
}
