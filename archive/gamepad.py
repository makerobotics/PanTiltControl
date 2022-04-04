from inputs import get_gamepad
from inputs import devices
from inputs import get_key

while 1:
    try:
        #events = devices.gamepads[0]._do_iter()
        #if events is not None:            
        #    for event in events:
        #        print(event.code+": "+str(event.state))
        #events = get_gamepad()
        events = get_key()
        for event in events:
            #print(event.ev_type, event.code, event.state)
            #print("code : "+event.code) # axis
            #print(event.state) # value
            #if("ABS" in event.code):
            print(event.code+": "+str(event.state))
    except KeyboardInterrupt:
        # Signal termination
        print("")
        break