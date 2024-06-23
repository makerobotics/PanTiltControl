let ws;
let lastMove = Date.now();
let speed = 1;
let stop = 0;
let pos_x = 0;
let pos_y = 0;
let tgt_x = 0;
let tgt_y = 0;

function init() {
    console.log("Init");
    WebSocketControl();
    document.getElementById("video").addEventListener("click", setPosition, false);
    // handle enter pressed in input box
    textInput = document.getElementById('input');
    textInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        //console.log('Enter key pressed!');
        sendMessage();
      }
    });
};

function handleVideoCheckboxClick(cb) {
    if(cb.checked){
        ws.send("video;on");
        log('Tx: Video on');
    }
    else{
        ws.send("video;off");
        log('Tx: Video off');
    }
}

function WebSocketControl() {
    if ("WebSocket" in window) {

        ws = new WebSocket('ws://' + location.host + "/websocket");

        ws.onopen = function () {

            document.getElementById("input").style.backgroundColor = "green";
            log('Connection opened');
            // Start timer to get positions
            setInterval(getPositions, 2000);
            // Turn off stepper to avoid heating
            sendCommand("4 6 0");
            stop = 1;
            // Set to relative position control
            sendCommand("4 7 0");
        };

        ws.onmessage = function (evt) {
            var obj;
            const re_position = /(-?[\d]+)\s(-?[\d]+)/;
            //console.log(evt.data);
            if(evt.data.includes("{")){
                try {
                    obj = JSON.parse(evt.data);
                } catch (e) {
                    console.error("Syntax error in Json string");
                }
            }
            else{
                //document.getElementById('log').innerHTML += 'Rx: '+evt.data+'\n';
                //log('Rx: '+evt.data);
                if(evt.data.length>20)
                  document.getElementById("video").src = "data:image/jpeg;base64," + evt.data;
                else{
                    try {
                        match = evt.data.match(re_position);
                        document.getElementById("position").value = `x: ${match[1]} / y: ${match[2]}`;
                        pos_x = Number(match[1]);
                        pos_y = Number(match[2]);
                        if(pos_x==tgt_x && pos_y== tgt_y){
                            log("standstill")
                        }
                    }
                    catch(e) {
                    }
                    finally {
                        log('Rx: '+evt.data);
                    }
                }
            }
        };

        ws.onerror = function (event) {
            console.error("WebSocket error observed:", event);
            log('Error: ' + event.data);
        };

        ws.onclose = function () {
            document.getElementById("input").style.backgroundColor = "red";
            log('Connection closed');
        };
    } else {
        // The browser doesn't support WebSocket
        alert("WebSocket NOT supported by your Browser!");
    }
}

function log(line) {
    document.getElementById('log').innerHTML = document.getElementById('log').innerHTML + line + '\n';
    document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight;
}

function clearLog() {
    document.getElementById('log').innerHTML = '';
}

function getPositions(){
    sendCommand("5 4", false);
}

function setPosition(e){
    let horrizontal;
    let vertical;
    let h_factor;
    let v_factor;

    //console.log(e.offsetX, e.offsetY, e.target.clientWidth, e.target.clientHeight);
    horrizontal = e.offsetX-e.target.clientWidth/2;
    vertical = -(e.offsetY-e.target.clientHeight/2);
    h_factor = document.getElementById("h_factor").value;
    v_factor = document.getElementById("v_factor").value;
    //log("x: "+horrizontal+", y: "+vertical);
    sendCommand('1 '+(horrizontal*h_factor) + ' ' + (-vertical*v_factor), true);
    tgt_x = tgt_x + horrizontal*h_factor;
    tgt_y = tgt_y + vertical*v_factor;
}

// used by manual command on GUI
function sendMessage() {
    const command = document.getElementById('input').value;
    sendCommand(command);
    //document.getElementById('input').value = '';
}

function sendCommand(command, logit=true){
    if(ws != null){
        ws.send(command);
    }
    if(logit){
        log('Tx: '+command);
    }
}

function setSpeed(s){
    speed = s;
}

function toggleStop(){
    if(stop==0){
      sendCommand("4 6 0"); // turn off enable pin
      stop = 1;
    }
    else{ 
      sendCommand("4 6 1");
      stop = 0;
    }
}
