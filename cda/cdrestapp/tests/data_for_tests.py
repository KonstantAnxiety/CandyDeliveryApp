valid_couriers = {
    "data": [
        {
            "courier_id": 4,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        },
        {
            "courier_id": 5,
            "courier_type": "bike",
            "regions": [22],
            "working_hours": ["09:00-18:00"]
        }
    ]
}

invalid_couriers = {
    "data": [
        {
            "courier_id": 6,
            "courier_type": "asdf",
            "regions": [],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        },
        {
            "courier_id": 7,
            "courier_type": "bike",
            "regions": [0],
            "working_hours": []
        }
        ,
        {
            "courier_id": 8,
            "regions": [-1, 6.9],
            "working_hours": ["INVALID_TIME_FORMAT"]
        }
    ]
}

valid_courier_patch = {
    "regions": [11, 33, 2]
}

valid_orders = {
    "data": [
        {
            "order_id": 1,
            "weight": 50,
            "region": 12,
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 2,
            "weight": 15,
            "region": 1,
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 3,
            "weight": 0.01,
            "region": 22,
            "delivery_hours": ["09:00-12:00", "16:00-21:30"]
        }
    ]
}

invalid_orders = {
    "data": [
        {
            "order_id": 4,
            "weight": 50,
            "region": 0,
            "delivery_hours": []
        },
        {
            "order_id": 5,
            "weight": 15,
            "region": -1,
            "delivery_hours": ["INVALID_TIME_FORMAT"]
        },
        {
            "order_id": 6,
            "weight": 0.01,
            "region": 22
        }
    ]
}

valid_assign = {
    "courier_id": 1
}

invalid_assign = {
    "courier_id": -1
}

valid_complete = {
    "courier_id": 1,
    "order_id": 3,
    "complete_time": "2021-01-10T10:33:01.42Z"
}
