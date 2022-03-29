from inputs import get_gamepad
while 1:
    try:
        events = get_gamepad()
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