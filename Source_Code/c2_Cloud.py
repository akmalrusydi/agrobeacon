import json
import time
import paho.mqtt.client as mqtt

# =========================================================
# THINGSBOARD CONFIG
# =========================================================

THINGSBOARD_HOST = "thingsboard.cloud"

ACCESS_TOKEN = "RlPO4148IG3Mvm7BYrm8"

PORT = 1883

# =========================================================
# MQTT CLIENT
# =========================================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION1
)

client.username_pw_set(
    ACCESS_TOKEN
)

# =========================================================
# CONNECTION STATUS
# =========================================================

connected = False

# =========================================================
# CONNECT CALLBACK
# =========================================================

def on_connect(
    client,
    userdata,
    flags,
    rc
):

    global connected

    if rc == 0:

        connected = True

        print(
            "ThingBoard Connected"
        )

    else:

        connected = False

        print(
            "ThingBoard Connection Failed:",
            rc
        )

# =========================================================
# DISCONNECT CALLBACK
# =========================================================

def on_disconnect(
    client,
    userdata,
    rc
):

    global connected

    connected = False

    print(
        "ThingBoard Disconnected"
    )

# =========================================================
# CALLBACK REGISTER
# =========================================================

client.on_connect = on_connect

client.on_disconnect = on_disconnect

# =========================================================
# CONNECT FUNCTION
# =========================================================

def connect_tb():

    global connected

    try:

        client.connect(
            THINGSBOARD_HOST,
            PORT,
            60
        )

        client.loop_start()

        # =============================================
        # WAIT CONNECT
        # =============================================

        timeout = 5

        start = time.time()

        while not connected:

            if (
                time.time() - start >
                timeout
            ):

                print(
                    "ThingBoard Connect Timeout"
                )

                return False

            time.sleep(0.1)

        return True

    except Exception as e:

        print(
            "TB CONNECT ERROR:",
            e
        )

        return False

# =========================================================
# RECONNECT
# =========================================================

def reconnect_tb():

    global connected

    if connected:

        return True

    print(
        "Reconnecting ThingBoard..."
    )

    try:

        client.loop_stop()

    except:

        pass

    try:

        client.disconnect()

    except:

        pass

    time.sleep(1)

    return connect_tb()

# =========================================================
# SEND TELEMETRY
# =========================================================

def send_data(data):

    global connected

    try:

        # =============================================
        # CHECK CONNECTION
        # =============================================

        if not connected:

            print(
                "MQTT Not Connected"
            )

            reconnect_tb()

            if not connected:

                return False

        # =============================================
        # JSON PAYLOAD
        # =============================================

        payload = json.dumps(data)

        # =============================================
        # PUBLISH
        # =============================================

        result = client.publish(

            "v1/devices/me/telemetry",

            payload,

            qos=1
        )

        # =============================================
        # WAIT MQTT COMPLETE
        # =============================================

        result.wait_for_publish()

        # =============================================
        # STATUS
        # =============================================

        if result.is_published():

            return True

        else:

            print(
                "Telemetry Publish Failed"
            )

            connected = False

            return False

    except Exception as e:

        print(
            "TB SEND ERROR:",
            e
        )

        connected = False

        return Falseimport json
import time
import paho.mqtt.client as mqtt

# =========================================================
# THINGSBOARD CONFIG
# =========================================================

THINGSBOARD_HOST = "thingsboard.cloud"

ACCESS_TOKEN = "RlPO4148IG3Mvm7BYrm8"

PORT = 1883

# =========================================================
# MQTT CLIENT
# =========================================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION1
)

client.username_pw_set(
    ACCESS_TOKEN
)

# =========================================================
# CONNECTION STATUS
# =========================================================

connected = False

# =========================================================
# CONNECT CALLBACK
# =========================================================

def on_connect(
    client,
    userdata,
    flags,
    rc
):

    global connected

    if rc == 0:

        connected = True

        print(
            "ThingBoard Connected"
        )

    else:

        connected = False

        print(
            "ThingBoard Connection Failed:",
            rc
        )

# =========================================================
# DISCONNECT CALLBACK
# =========================================================

def on_disconnect(
    client,
    userdata,
    rc
):

    global connected

    connected = False

    print(
        "ThingBoard Disconnected"
    )

# =========================================================
# CALLBACK REGISTER
# =========================================================

client.on_connect = on_connect

client.on_disconnect = on_disconnect

# =========================================================
# CONNECT FUNCTION
# =========================================================

def connect_tb():

    global connected

    try:

        client.connect(
            THINGSBOARD_HOST,
            PORT,
            60
        )

        client.loop_start()

        # =============================================
        # WAIT CONNECT
        # =============================================

        timeout = 5

        start = time.time()

        while not connected:

            if (
                time.time() - start >
                timeout
            ):

                print(
                    "ThingBoard Connect Timeout"
                )

                return False

            time.sleep(0.1)

        return True

    except Exception as e:

        print(
            "TB CONNECT ERROR:",
            e
        )

        return False

# =========================================================
# RECONNECT
# =========================================================

def reconnect_tb():

    global connected

    if connected:

        return True

    print(
        "Reconnecting ThingBoard..."
    )

    try:

        client.loop_stop()

    except:

        pass

    try:

        client.disconnect()

    except:

        pass

    time.sleep(1)

    return connect_tb()

# =========================================================
# SEND TELEMETRY
# =========================================================

def send_data(data):

    global connected

    try:

        # =============================================
        # CHECK CONNECTION
        # =============================================

        if not connected:

            print(
                "MQTT Not Connected"
            )

            reconnect_tb()

            if not connected:

                return False

        # =============================================
        # JSON PAYLOAD
        # =============================================

        payload = json.dumps(data)

        # =============================================
        # PUBLISH
        # =============================================

        result = client.publish(

            "v1/devices/me/telemetry",

            payload,

            qos=1
        )

        # =============================================
        # WAIT MQTT COMPLETE
        # =============================================

        result.wait_for_publish()

        # =============================================
        # STATUS
        # =============================================

        if result.is_published():

            return True

        else:

            print(
                "Telemetry Publish Failed"
            )

            connected = False

            return False

    except Exception as e:

        print(
            "TB SEND ERROR:",
            e
        )

        connected = False

        return False
