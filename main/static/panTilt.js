let ws;
let lastMove = Date.now();
let speed = 1;

// Create JoyStick object into the DIV 'joy1Div'
var Joy1 = new JoyStick('joy1Div', {}, function(stickData) {
    if((Date.now()-lastMove)>200){
        sendCommand('4 1 '+(-stickData.y*speed) + ' ' + (-stickData.x*speed), false);
        lastMove = Date.now();
    }
});

function init() {
    console.log("Init");
    WebSocketControl();
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
            //setInterval(getPositions, 500);
        };

        ws.onmessage = function (evt) {
            var obj;
            //console.log(evt.data);
            if(evt.data.includes("{")){
                try {
                    obj = JSON.parse(evt.data);
                    /*document.getElementById('dist').value = obj.distance;
                    document.getElementById('speedleft').value = obj.speedL;
                    document.getElementById('posleft').value = obj.encoderL;
                    document.getElementById('speedright').value = obj.speedR;
                    document.getElementById('posright').value = obj.encoderR;
                    document.getElementById('yaw').value = obj.yaw;
                    document.getElementById('odo').value = obj.odoDistance;*/
                } catch (e) {
                    console.error("Syntax error in Json string");
                }
            }
            else{
                //document.getElementById('log').innerHTML += 'Rx: '+evt.data+'\n';
                //log('Rx: '+evt.data);
                document.getElementById("video").src = "data:image/jpeg;base64," + evt.data;
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
