
import requests


def create_adv():
    response = requests.post('http://127.0.0.1:8080/adv', json={'title': 'title3',
                                                                'description': 'description3',
                                                                'owner': 'owner3'
})
    print(response.text)
    data = response.json()
    print(data)


def get_adv():
    response = requests.get('http://127.0.0.1:8080/adv/3')
    print(response.text)


def get_health():
    response = requests.get('http://127.0.0.1:8080/')
    print(response.text)


def upd_adv():
    response = requests.patch('http://127.0.0.1:8080/adv/3', json={'owner': 'new_owner'})
    print(response.text)


def del_adv():
    response = requests.delete('http://127.0.0.1:8080/adv/3')
    print(response.text)

# get_health()
# create_adv()
get_adv()
# upd_adv()
# del_adv()
