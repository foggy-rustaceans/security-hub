from lib2to3.pytree import LeafPattern
from os import stat
from tkinter import *
from tkcalendar import *
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
import os
import json
from azure.iot.device import IoTHubDeviceClient
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobClient
from azure.iot.device import Message, MethodResponse
import time

CONNECTION_STRING = "HostName=SecurityHub.azure-devices.net;DeviceId=imageUpload;SharedAccessKey=iYUDLdBLf6+nkDxECZt6x9LaMennH/+XZmbSxHiPuio="
PIN_CONNECTION_STRING = "HostName=SecurityHub.azure-devices.net;DeviceId=pinUpload;SharedAccessKey=IBWPe06RbaJ1xgOhKhgQ54rHQi08sWv9IF3fa1yRG4Q="
ACCESS_CONNECTION_STRING = "HostName=SecurityHub.azure-devices.net;DeviceId=accessControl;SharedAccessKey=WTnBv7+1SgRsFOHC9LANtTcipfyrvpGgKe5sBgFFWfg="

ACCESS_COLOR = "red"
ACCESS_MESSAGE = "ACCESS DENIED"

DEFAULT_HEIGHT = 300

photo_device = IoTHubDeviceClient.create_from_connection_string(
    CONNECTION_STRING)

pin_device = IoTHubDeviceClient.create_from_connection_string(
    PIN_CONNECTION_STRING)

access_device = IoTHubDeviceClient.create_from_connection_string(
    ACCESS_CONNECTION_STRING)

root = Tk()
frame_left = Frame(root)
frame_left.pack(side=LEFT)
frame_right = Frame(root)
frame_right.pack(side=RIGHT)
frame_center = Frame(root)
frame_center.pack(side=RIGHT)
button_quit = Button(frame_left, text='Exit Program', command=root.quit)
button_quit.pack()

camera_label = Label(frame_left, text='Please Stand in Front of the Camera')
camera_label.pack()

my_label = Label(frame_left)
my_label.pack()
link = "./default.png"


def resize(img):
    w, h = img.size
    lmb = DEFAULT_HEIGHT/h
    return img.resize((int(w*lmb), int(h * lmb)))


my_img = ImageTk.PhotoImage(resize(Image.open(link)))
my_label.configure(image=my_img)
my_label.image = my_img


def myClick():
    link = askopenfilename()
    run_sample(photo_device, link)
    my_img = ImageTk.PhotoImage(resize(Image.open(link)))
    my_label.configure(image=my_img)
    my_label.image = my_img


def store_blob(blob_info, file_name):
    try:
        sas_url = "https://{}/{}/{}{}".format(
            blob_info["hostName"],
            blob_info["containerName"],
            blob_info["blobName"],
            blob_info["sasToken"]
        )

        print("\nUploading file: {} to Azure Storage as blob: {} in container {}\n".format(
            file_name, blob_info["blobName"], blob_info["containerName"]))

        # Upload the specified file
        with BlobClient.from_blob_url(sas_url) as blob_client:
            with open(file_name, "rb") as f:
                result = blob_client.upload_blob(f, overwrite=True)
                return (True, result)

    except FileNotFoundError as ex:
        # catch file not found and add an HTTP status code to return in notification to IoT Hub
        ex.status_code = 404
        return (False, ex)

    except AzureError as ex:
        # catch Azure errors that might result from the upload operation
        return (False, ex)


def run_sample(photo_device, path):
    # Connect the client
    photo_device.connect()

    # Get the storage info for the blob
    blob_name = os.path.basename(path)
    storage_info = photo_device.get_storage_info_for_blob(blob_name)

    # Upload to blob
    success, result = store_blob(storage_info, path)

    if success == True:
        print("Upload succeeded. Result is: \n")
        print(result)
        print()

        photo_device.notify_blob_upload_status(
            storage_info["correlationId"], True, 200, "OK: {}".format(
                path)
        )

    else:
        # If the upload was not successful, the result is the exception object
        print("Upload failed. Exception is: \n")
        print(result)
        print()

        photo_device.notify_blob_upload_status(
            storage_info["correlationId"], False, result.status_code, str(
                result)
        )


def show():
    label.config(text=clicked.get())


myButton = Button(frame_left, text='Upload Image', command=myClick)
myButton.pack()

pin_entry = Entry(frame_left)
pin_entry.pack()


def enter_pin():
    msg = {"pin": pin_entry.get()}
    msg = Message(json.dumps(msg))
    msg.content_encoding = "utf-8"
    msg.content_type = "application/json"
    pin_device.send_message(msg)


pin_button = Button(frame_left, text='Enter PIN', command=enter_pin)
pin_button.pack()

# Dropdown menu options
options = [
    "Rochester",
    "Binghampton",
    "Ithaca",
]

# datatype of menu text
clicked = StringVar()

# initial menu text
clicked.set("Rochester")

# Create Dropdown menu
drop = OptionMenu(frame_left, clicked, *options)
drop.pack()

# Create button, it will change label text
button = Button(frame_left, text="click Me", command=show).pack()

# Create Label
label = Label(frame_left, text=" ")
label.pack()

status_label = Label(frame_right, text='Status:')
status_label.pack()
entry_label = Label(frame_right, text=ACCESS_MESSAGE,
                    bg=ACCESS_COLOR, padx=60, pady=60)
entry_label.pack()


def method_request_handler(method_request):
    if method_request.name == "grantAccess":
        try:
            print(method_request.name)
            global ACCESS_COLOR
            ACCESS_COLOR = "Green"
            global ACCESS_MESSAGE
            ACCESS_MESSAGE = "ACCESS GRANTED"
            # entry_label.config(text="ACCESS GRANTED")
        except ValueError:
            print("here 1")
            response_payload = {"Response": "Invalid parameter"}
            response_status = 400
        else:
            print("here 2")
            response_payload = {
                "Response": "Executed direct method {}".format(method_request.name)}
            response_status = 200
    else:
        print("here 3")
        response_payload = {
            "Response": "Direct method {} not defined".format(method_request.name)}
        response_status = 404

    method_response = MethodResponse.create_from_method_request(
        method_request, response_status, response_payload)
    access_device.send_method_response(method_response)


try:
    access_device.on_method_request_received = method_request_handler
except:
    access_device.shutdown()
    raise

hour_string = StringVar()
min_string = StringVar()
last_value_sec = ""
last_value = ""
f = ('Times', 20)


def display_msg():
    date = cal.get_date()
    m = min_sb.get()
    h = sec_hour.get()
    s = sec.get()
    t = f"Current time is {date} at {m}:{h}:{s}."
    msg_display.config(background="light blue")
    msg_display.config(text=t)


if last_value == "59" and min_string.get() == "0":
    hour_string.set(int(hour_string.get()) +
                    1 if hour_string.get() != "23" else 0)
    last_value = min_string.get()

if last_value_sec == "59" and sec_hour.get() == "0":
    min_string.set(int(min_string.get())+1 if min_string.get() != "59" else 0)
if last_value == "59":
    hour_string.set(int(hour_string.get()) +
                    1 if hour_string.get() != "23" else 0)
    last_value_sec = sec_hour.get()

fone = Frame(frame_right)
ftwo = Frame(frame_right)

fone.pack(pady=10)
ftwo.pack(pady=10)

cal = Calendar(
    fone,
    selectmode="day",
    year=2021,
    month=2,
    day=3
)
cal.pack()

min_sb = Spinbox(
    ftwo,
    from_=0,
    to=23,
    wrap=True,
    textvariable=hour_string,
    width=2,
    state="readonly",
    font=f,
    justify=CENTER
)
sec_hour = Spinbox(
    ftwo,
    from_=0,
    to=59,
    wrap=True,
    textvariable=min_string,
    font=f,
    width=2,
    justify=CENTER
)

sec = Spinbox(
    ftwo,
    from_=0,
    to=59,
    wrap=True,
    textvariable=sec_hour,
    width=2,
    font=f,
    justify=CENTER
)

min_sb.pack(side=LEFT, fill=X, expand=True)
sec_hour.pack(side=LEFT, fill=X, expand=True)
sec.pack(side=LEFT, fill=X, expand=True)

msg = Label(
    frame_right,
    text="Hour  Minute  Seconds",
    font=("Times", 12),
    bg="light blue"
)
msg.pack(side=TOP)

actionBtn = Button(
    frame_right,
    text="Enter Time",
    padx=10,
    pady=10,
    command=display_msg
)
actionBtn.pack(pady=10)

msg_display = Label(
    frame_right,
    text=""
)
msg_display.pack(pady=10)

access_device.connect()
while True:
    time.sleep(1/20)
    entry_label.config(text=ACCESS_MESSAGE, background=ACCESS_COLOR)
    # print(entry_label.cget("bg"))
    root.update()

root.mainloop()
