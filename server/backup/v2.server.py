# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID
# Student: John Doe
# ------------------------------------------------------------------------------------------------------
import traceback
import sys
import time
import json
import argparse
from threading import Thread

from bottle import Bottle, run, request, template
import requests
# ------------------------------------------------------------------------------------------------------
try:
    app = Bottle()

    board = {0:"nothing"} 


    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def add_new_element_to_store(entry_sequence, element, is_propagated_call=False):
        global board, node_id
        success = False
        try:
            board[entry_sequence] = element
            success = True
        except Exception as e:
            print e
        return success

    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call = False):
        global board, node_id
        success = False
        try:
            board[entry_sequence] = modified_element
            success = True
        except Exception as e:
            print e
        return success

    def delete_element_from_store(entry_sequence, is_propagated_call = False):
        global board, node_id
        success = False
        try:
            board.pop(entry_sequence)  
            success = True
        except Exception as e:
            print e
        return success

    # ------------------------------------------------------------------------------------------------------
    # DISTRIBUTED COMMUNICATIONS FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def contact_vessel(vessel_ip, path, payload=None, req='POST'):
        # Try to contact another server (vessel) through a POST or GET, once
        success = False
        try:
            if 'POST' in req:
                res = requests.post('http://{}{}'.format(vessel_ip, path), data=payload)
            elif 'GET' in req:
                res = requests.get('http://{}{}'.format(vessel_ip, path))
            else:
                print 'Non implemented feature!'
            # result is in res.text or res.json()
            #print(res.text)
            print "res_code is {}".format(res.status_code)
            if res.status_code == 200:
                success = True
        except Exception as e:
            print e
        return success

    def propagate_to_vessels(path, payload = None, req = 'POST'):
        global vessel_list, node_id
        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id: # don't propagate to yourself
                success = contact_vessel(vessel_ip, path, payload, req)
                if not success:
                    print "\nCould not contact vessel {}\n".format(vessel_id)


    # ------------------------------------------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------------------------------------------
    # a single example (index) should be done for get, and one for post
    # ------------------------------------------------------------------------------------------------------
    @app.route('/')
    def index():
        global board, node_id
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()), \
                                            members_name_string='lhan@student.chalmers.se;shahn@student.chalmers.se')

    @app.get('/board')
    def get_board():
        global board, node_id
        print board  #no input, print nothing
        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()))
    # ------------------------------------------------------------------------------------------------------
    @app.post('/board')
    def client_add_received():
        '''Adds a new element to the board,Called directly when a user is doing a POST request on /board'''
        global board, node_id, LC
        try:
            new_entry = request.forms.get('entry') # new_entry is the user input from webpage,change board value from nothing to new_entry
            # propagate threads to avoid blocking,create the thread as a deamon
            LC = LC + 1
            print "node_id is {}, LC is {}".format(node_id,LC)
            add_new_element_to_store(LC, new_entry) 
            board_dict = {LC : new_entry}
            t = Thread(target=propagate_to_vessels, args = ('/propagate/add/{}'.format(LC),board_dict[LC],'POST')) 
            t.daemon = True
            t.start()
            return True
        except Exception as e:
            print e
        return False

    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        global board, node_id,LC
        try:
            # try to get user click, action_dom is action delete or modify
            action_dom = request.forms.get('delete') 
            if int(action_dom) == 0:
                modified_element = request.forms.get('entry') 
                modify_element_in_store(element_id, modified_element, is_propagated_call = False)
                propagate_to_vessels('/propagate/modify/{}'.format(element_id),modified_element,'POST')
            elif int(action_dom) == 1:
                delete_element_from_store(element_id)
                propagate_to_vessels('/propagate/delete/{}'.format(element_id))
            return True
        except Exception as e:
            print e
        return False

    @app.post('/propagate/<action>/<element_id:int>')
    def propagation_received(action, element_id):
        # check the action is add, modify or delete
        global board, node_id, LC
        try:
            if action == 'add':
                body = request.body.read()
                print "my nodeid is {}, my LC is {}, the event trigger me LC is {}".format(node_id,LC,element_id)
                if LC > element_id:
                    LC = LC + 1
                else:
                    LC = element_id + 1
                print "new LC is {}".format(LC)
                add_new_element_to_store(LC, body) # you might want to change None here
            elif action =='modify':
                body = request.body.read()
                modify_element_in_store(element_id, body)
            elif action == 'delete':
                delete_element_from_store(element_id)
            template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()))
            return True
        except Exception as e:
            print e
        return False

        
    # ------------------------------------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------------------------------------
    # Execute the code
    def main():
        global vessel_list, node_id, app, LC
        LC = 0
        port = 80
        parser = argparse.ArgumentParser(description='Your own implementation of the distributed blackboard')
        parser.add_argument('--id', nargs='?', dest='nid', default=1, type=int, help='This server ID')
        parser.add_argument('--vessels', nargs='?', dest='nbv', default=1, type=int, help='The total number of vessels present in the system')
        args = parser.parse_args()
        node_id = args.nid
        vessel_list = dict()
        # We need to write the other vessels IP, based on the knowledge of their number
        for i in range(1, args.nbv):
            vessel_list[str(i)] = '10.1.0.{}'.format(str(i))

        try:
            run(app, host=vessel_list[str(node_id)], port=port)
        except Exception as e:
            print e
    # ------------------------------------------------------------------------------------------------------
    if __name__ == '__main__':
        main()
except Exception as e:
        traceback.print_exc()
        while True:
            time.sleep(60.)