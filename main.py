from os import system, name
import pymysql
from tabulate import tabulate
import pandas as pd

sql_calls={
    "login":"call login(%s, %s);",
    'all usernames':'call get_all_usernames();',
    "sign up": "call create_new_user(%s, %s, %s, %s);",
    "shows": "call get_all_shows();",
    'actors':'call get_all_actors();',
    'genres':'call get_all_genres();',
    'networks':'call get_all_networks();',
    'get show':'call get_show_by_name(%s)',
    'show reviews': 'call get_show_reviews(%s);',
    'add review':'call add_review(%s, %s, %s, %s);',
    'update review': 'call update_review(%s, %s, %s, %s);',
    'delete review': 'call delete_review(%s, %s);',
    'actor name': 'call get_actor_by_name(%s);',
    'genre name': 'call get_genre_by_name(%s);',
    'network name':'call get_network_by_name(%s);'
}


def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

def display_data(data):
    for row in data:
        out = "| "
        for i in row.values():
            out += str(i) + ' | '
        print(out)



def review_helper(con, cur, username, series_ID):
    def update_review(con, cur, username, series_ID, old_review):
        clear()
        print('here is your current review')
        display_data([old_review])
        cur.execute(sql_calls['update review'],
                    (username, series_ID, input('enter your new rating:\n'), input('enter your new comment:\n')))
        con.commit()
        return

    def delete_review(con, cur, username, series_ID, old_review):
        clear()
        print('here is your current review')
        display_data([old_review])
        if input('are you sure you want to delete your review? (y/n)\n') == 'y':
            cur.execute(sql_calls['delete review'], (username, series_ID))
            con.commit()

    while True:
        clear()
        cur.execute(sql_calls['show reviews'], (series_ID))
        reviews = cur.fetchall()
        display_data(reviews)

        user_review = None

        for row in reviews:
            if row['username'] == username:
                user_review = row

        while True:
            if user_review is not None:
                print('you have already made a review. you can edit or delete your review')
            else:
                print('type review to make a new review for this show')

            command = input('you can also type return to view the show page again\n')
            if command == 'return':
                return
            elif command == 'edit' and user_review is not None:
                update_review(con, cur, username, series_ID, user_review)
                break
            elif command == 'delete' and user_review is not None:
                delete_review(con, cur, username, series_ID, user_review)
                break
            elif command == 'review' and user_review is None:
                cur.execute(sql_calls['add review'], (username, series_ID, input('rate the show on a scale from 1-10:\n'),
                                                      input('write a comment about the show:\n')))
                con.commit()
                break
            else:
                print('please enter a valid command')



def show_pages(con, cur, username, field):

    cur.execute(sql_calls['shows'])
    rows = cur.fetchall()

    while True:
        clear()
        display_data(rows)
        command = input('name a show to view or type exit to return to main menu: ')

        if command == 'exit':
            return

        cur.execute(sql_calls['get show'], (command))
        clear()
        show = cur.fetchall()
        if show is None or show[0]['series_ID'] is None:
            print('no show exists with this name')
            pass
        display_data(show)
        see_reviews = input('type review to see reviews, or press any key to see all shows: ')
        if see_reviews != 'review':
            continue
        review_helper(con, cur, username, show[0]['series_ID'])




def other_pages(cnx, cur, username, field):
    cur.execute(sql_calls[field+'s'])
    rows = cur.fetchall()

    input_string = ''
    if field == 'actor':
        input_string = 'name an actor to view or type exit to return to main menu: '
    else:
        input_string = 'name a {field} to view or type exit to return to main menu: '.format(field=field)

    while True:
        clear()
        display_data(rows)
        command = input(input_string)

        if command == 'exit':
            return

        cur.execute(sql_calls[field+' name'], (command))
        clear()
        row = cur.fetchall()
        if row is None:
            print('no {field} exists with this name'.format(field=field))
            pass
        display_data(row)
        input('press any key to see all {field}s: '.format(field=field))

def login(cnx, cur):
    while True:
        cur.execute(sql_calls['login'], (input("username: "), input('password: ')))

        validate = cur.fetchall()

        if 'error_message' in validate:
            print(validate['error_message'])
            pass
        else:
            return main_menu(cnx, cur, validate[0]['username'])

def signup(cnx, cur):
    clear()
    cur.execute(sql_calls['all usernames'])
    vals = cur.fetchall()
    usernames = []
    for row in vals:
        usernames.append(row['username'])
    while True:
        u = input('create your username: ')
        if u in usernames:
            clear()
            print('this username has alread been taken')
            continue
        p = input('please create your password: ')
        fname = input('please enter your first name: ')
        lname = input('please enter your last name: ')

        cur.execute(sql_calls['sign up'], (u, p, fname, lname))
        cnx.commit()
        return main_menu(cnx, cur, u)

functions={
    'show':show_pages,
    'actor':other_pages,
    'genre': other_pages,
    'network':other_pages,
    'login': login,
    'signup':signup
}

def login_sequence():
    uname = input('Enter mysql username: ')
    pword = input('Enter mysql password: ')

    try:
        cnx = pymysql.connect(host='localhost', user=uname, password=pword, db='tvshows',
                              charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    except:
        print('incorrect username or password')
        return
    cur = cnx.cursor()

    print('welcome!\nplease log in or sign up')

    while True:
        c = input()
        try:
            functions[c](cnx, cur)
            break
        except KeyError:
            print('please select login or signup')
        except Exception as e:
            print(e)
            break

    cur.close()
    cnx.close()

def main_menu(cnx, cur, username):
    clear()
    print('welcome {username}!'.format(username=username))

    while True:
        print('please enter what you\'d like to view from the database\n'
          'your options are: shows, actors, genres, or networks')

        try:
            c = input('type quit to exit the program\n')
            if c == 'quit':
                print('Thanks!')
                return
            clear()
            functions[c](cnx, cur, username, c)
        except KeyError:
            clear()
            print('please enter a valid command')


login_sequence()