import logging
import random

import azure.functions as func
from twilio.rest import Client

account_sid = "AC801aa772453d06d7c7be40dc65667b19"
auth_token = "5b8ae484037bd446b3a1900255cb2d28"
twilio_number = "+17372019218"

client = Client(account_sid, auth_token)

jkt_info_cmd = "JKT"
cmd_separator = ','
arg_separator = '='

BAD_HOOD = "RED_HD"
BAD_WATERPROOF = "RED_WP"
BAD_PRECIP = "RED_PCP"
BAD_HIGH_TEMP = "RED_H"
BAD_LOW_TEMP = "RED_L"
CMD_STATE_BAD_HOOD = "STATE_{}".format(BAD_HOOD)
CMD_STATE_BAD_WATERPROOF = "STATE_{}".format(BAD_WATERPROOF)
CMD_STATE_BAD_PRECIP = "STATE_{}".format(BAD_PRECIP)
CMD_STATE_BAD_HIGH_TEMP = "STATE_{}".format(BAD_HIGH_TEMP)
CMD_STATE_BAD_LOW_TEMP = "STATE_{}".format(BAD_LOW_TEMP)
CMD_STATE_GOOD = "STATE_GREEN"

hood = 'HD'
high_temp = 'H'
low_temp = 'L'
waterproof = 'WP'
windproof = 'W'

def main(req):
    logging.info('Python HTTP trigger function processed a request.')
    
    req_body = req.params

    logging.info('Request Body: {}'.format(req_body))
    command_sid = None
    try:
        command_sid = req_body['CommandSid']
    except:
        pass
    command = req_body['Command']
    # Check if command type is one of the defined
    if command_sid == jkt_info_cmd:
        # Get weather
        current_temp = None
        is_raining = None
        try:
            current_temp = int(req_body['Temp'])
            is_raining = bool(req_body['Precipitation'])
        except:
            logging.error('Unable to retrieve current temp and precip...')
            return func.HttpResponse(status_code=200)

        logging.info('Current temp: {} - Raining: {}'.format(current_temp, is_raining))

        jacket_info = {}
        is_good_for_weather = False
        bad_weather_reason = ''
        
        #  Parse jacket info
        split_cmd = command.split(cmd_separator)
        logging.info('Split command: {}'.format(split_cmd))
        for arg in split_cmd:
            split_arg = arg.split(arg_separator)
            
            logging.info('Split arg: {}'.format(split_arg))
            # We should have 2 parts to an argument in a cmd
            if len(split_arg) < 2:
                logging.info('skipping!')
                continue
            
            # Check if waterproof, high/low temp
            try:
                jacket_info[split_arg[0]] = int(split_arg[1])
            except Exception as e:
                logging.error(e)
                continue

        logging.info(jacket_info)
        # Determine jacket state
        # High and low state should not be empty
        if (not jacket_info[high_temp] and jacket_info[high_temp] != 0) or (not jacket_info[low_temp] and jacket_info[low_temp] != 0):
            return func.HttpResponse(status_code=200)
        
        if jacket_info[high_temp] < current_temp:
            is_good_for_weather = False
            bad_weather_reason = CMD_STATE_BAD_HIGH_TEMP
        elif jacket_info[low_temp] > current_temp:
            is_good_for_weather = False
            bad_weather_reason = CMD_STATE_BAD_LOW_TEMP
        else:
            is_good_for_weather = True

        if is_raining:
            # If it's raining with no hood or is not waterproof, they should not wear this jacket
            try:
                if not jacket_info[hood] or not jacket_info[waterproof]:
                    is_good_for_weather = False
                    if not jacket_info[waterproof] and not jacket_info[hood]:
                        bad_weather_reason = CMD_STATE_BAD_PRECIP
                    if not jacket_info[hood]:
                        bad_weather_reason = CMD_STATE_BAD_HOOD
                    elif not jacket_info[waterproof]:
                        bad_weather_reason = CMD_STATE_BAD_WATERPROOF
            except:
                is_good_for_weather = False
                bad_weather_reason = CMD_STATE_BAD_PRECIP
        
        sim_id = req_body['SimSid']
        jacket_state = 0
        if is_good_for_weather:
            jacket_state = CMD_STATE_GOOD
        else:
            jacket_state = bad_weather_reason

        logging.info("Jacket good for weather: {}\n Reason: {}".format(is_good_for_weather, bad_weather_reason))
        command = client.wireless.commands.create(
            sim=sim_id,
            command='{}'.format(jacket_state)
        )

        return func.HttpResponse("Done!")
    else:
        if command.startswith('STATE_'):
            logging.info('State Received!')
            bad_jacket_reason = None
            if command == CMD_STATE_BAD_HIGH_TEMP:
                bad_jacket_reason = "This jacket is too heavy for this weather"
            elif command == CMD_STATE_BAD_LOW_TEMP:
                bad_jacket_reason = "This jacket is too light for this weather"
            elif command == CMD_STATE_BAD_PRECIP:
                bad_jacket_reason = "It's going to rain, wear a waterproof jacket with a hood!"
            elif command == CMD_STATE_BAD_WATERPROOF:
                bad_jacket_reason = "It's going to rain, wear a waterproof jacket!"
            elif command == CMD_STATE_BAD_HOOD:
                bad_jacket_reason = "It's going to rain, wear a jacket with a hood!"
            elif command == CMD_STATE_GOOD:
                bad_jacket_reason = "Congrats, you made a great life choice. Life choice evaluations made possible by NB-IoT via T-Mobile, Twilio, and Microsoft."

            if bad_jacket_reason and len(bad_jacket_reason) > 0:
                logging.info('Reason: {}'.format(bad_jacket_reason))
                client.messages.create(
                    body=bad_jacket_reason,
                    from_=twilio_number,
                    to='+12033088111')
            
            return func.HttpResponse(status_code=200)
        
