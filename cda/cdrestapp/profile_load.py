import requests
import random
import time
import json
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--n', default=3, type=int,
                    help='Number of requests')
parser.add_argument('--init', default=50, type=int,
                    help='Number of items in the first payload')
parser.add_argument('--mult', default=2, type=int,
                    help='Multiplier for the number of items in the next payload')
parser.add_argument('--s', default=2, type=int,
                    help='Number of seconds tp sleep between requests')


def payload(n: int, m: int) -> dict:
    courier_types = ('car', 'bike', 'foot')
    t_start = range(10, 12)
    t_end = range(13, 23)
    data = {'data': []}
    for i in range(n, m + 1):
        new_courier = {
            'courier_id': i,
            'courier_type': random.choice(courier_types),
            'regions': [random.randint(1, 100) for _ in range(random.randint(1, 6))],
            'working_hours': [f'{str(random.choice(t_start))}:00-{str(random.choice(t_end))}:00']
        }
        data['data'].append(new_courier)
    return data


def post_couriers(data: dict):
    url = 'http://localhost:8000/couriers'
    headers = {'Content-Type': 'application/json'}
    requests.post(url, json.dumps(data), headers=headers)


if __name__ == '__main__':
    args = parser.parse_args()
    start, end = 1, args.init
    for i in range(args.n):
        print(f'#{i + 1} Sending {start}-{end}...', end='', flush=True)
        data = payload(start, end)
        start = end + 1
        end = start + (i + 1) * args.init * args.mult - 1
        post_couriers(data)
        print('OK')
        if i < args.n - 1:
            time.sleep(args.s)
