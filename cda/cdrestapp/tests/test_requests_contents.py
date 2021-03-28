valid_courier_type = {
    "courier_type": "scooter",
    "capacity": 15,
    "earnings_coef": 7
}

invalid_courier_type = {
    "courier_type": "robot",
    "capacity": -1,
    "earnings_coef": -1
}

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
    "regions": [11, 33, 2],
    "courier_type": "car",
    "working_hours": ["11:35-14:05", "09:00-11:00"]
}

invalid_courier_patch = {
    "regions": [-1, 0, 1],
    "courier_type": "BAD_TYPE",
    "working_hours": [1230, "09:00"]
}

valid_orders = {
    "data": [
        {
            "order_id": 8,
            "weight": 50,
            "region": 12,
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 9,
            "weight": 15,
            "region": 1,
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 10,
            "weight": 0.01,
            "region": 22,
            "delivery_hours": ["09:00-12:00", "16:00-21:30"]
        }
    ]
}

invalid_orders = {
    "data": [
        {
            "order_id": 1.2,
            "weight": 50,
            "region": 0,
            "delivery_hours": []
        },
        {
            "order_id": -1.2,
            "weight": 15,
            "region": -1,
            "delivery_hours": ["INVALID_TIME_FORMAT"]
        },
        {
            "order_id": 0,
            "weight": 0.01,
            "region": 22
        }
    ]
}

valid_assign_one = {
    "courier_id": 1
}

valid_assign_two = {
    "courier_id": 2
}

invalid_assign = {
    "courier_id": -1
}

valid_complete = {
    "courier_id": 1,
    "order_id": 1,
    "complete_time": "2021-03-28T14:18:33.19Z"
}

invalid_complete = {
    "courier_id": 0,
    "order_id": "2",
    "complete_time": "According to all known laws of aviation,"
                     "there is no way a bee should be able to fly."
}
