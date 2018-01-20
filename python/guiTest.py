from serial import *
from tkinter import *
from fakeSerial import *
from barStatus import *
from dividedBarGraph import *
# The start of this code came from here Evan Boldt:
# http://robotic-controls.com/learn/python-guis/tkinter-serial


serialPorts = ["/dev/ttyUSB0", "/dev/ttyUSB1","/dev/ttyUSB2", "FAKE"]
baudRate = 115200

# This for loop attempts many different serial ports
for port in serialPorts:
    try:
        if port != "FAKE":
            ser = Serial(port , baudRate, timeout=0, writeTimeout=0) #ensure non-blocking
            print("Connecting to:", port, "... SUCCESS!")
        else:
            # If there are no serial ports, use fake serial to read from file
            print("Using Fake Serial")
            ser = FakeSerial( "test.txt")            
        break                   # once port is found, break from loop
    except:
        print("Cannot connect to:", port)



DEBUG = False
MAX_BUTTON_NUM = 4
BUTTON_NUM = 2
Qnum = 1
questions = [ ("Is Morality Objective or Subjective?", ["Subjective", "Other", "Objective"]),
              ("Do you like candy?", [ "Love it!", "Kind of", "sure?", "no"]),
              ("Do you like long questions that seem to go on and on and don't really have an end or meaning?", [ "Love it!", "Kind of", "sure?", "I only like really long, meaningless answers"]),
              ("Is there meaning in life?", ["yes", "no"])]

#labelsText = [["Subjective", "Other", "Objective"]' "3", "4", "5"] # labels for each bar graph

def toggleFullscreen(event):
    root.attributes("-fullscreen", root.attributes("-fullscreen") == 0)

def toggleDebug(event):
    global DEBUG
    DEBUG = not DEBUG
    if DEBUG:
        log.pack()
    else:
        log.pack_forget()

def step(event):
    global Qnum
    Qnum = (Qnum + 1) % len(questions)
    print("NEXT question please!")

    # update text
    canvas.itemconfig(question, text = questions[Qnum][0])
    
    # update voting stuff
    barStatus.changeLabels(questions[Qnum][1])
    divGraph.changeLabels(questions[Qnum][1])
    pass

#make a TkInter Window
root = Tk()
root.wm_title("Veritas Voting")
root.attributes("-fullscreen", True)
root.bind("<Control-w>", lambda e: root.destroy())
root.bind("<Escape>", toggleFullscreen)
root.bind("h", toggleDebug)
root.bind("b", step)
canvas = Canvas(root, width=1000, height=800, bg="#F3F3F1")
canvas.pack(fill=BOTH, expand=YES)
logo = PhotoImage(file='logo.png')
canvas.create_image(1000, 150, image=logo)

# make a text box to put the serial output
log = Text ( root, width=50, height=10, takefocus=0)
log.pack()
if not DEBUG:
    log.pack_forget()


# an array of arrays to store votes for each question/answer
votes =  [ [1 for i in range(len(x[1]))] for x in questions]
# votes = [1 for i in range(BUTTON_NUM)]

canVote =  [ [True for i in range(len(x[1]))] for x in questions] # keeps track if slider has reset yet
#canVote = [True for i in range(BUTTON_NUM)] # keeps track if slider has reset yet

# what stage is the button in (ie starting to vote, cooling down, at max/min)
status =  [ [0.0 for i in range(len(x[1]))] for x in questions]
#status = [0.0 for i in range(BUTTON_NUM)] # what stage is the button in (ie starting to vote, cooling down, at max/min)

offset = 200                                # offset between each of the bars
width = 50                      # of each bar
left = 1200                     # where to start the bars (from the left)
length = 450                    # max length of each bar
top =400                        # Where to start the bars





question = canvas.create_text(
    left/2, top +width/2 + offset, width = left, justify=CENTER,
    font=("Purisa-Bold", 70), anchor =CENTER, fill="#1E1E1E",
    text = questions[Qnum][0])




barStatus = BarStatus(canvas, (left,top), questions[Qnum][1])
divGraph = DividedBarGraph( canvas, (200, 900), questions[Qnum][1])


def updateAll(string):
    threshold = 40           # center point of when bar should move
    deadZone = 10            # prevent jitter (like a schmitt trigger)
    statStep = 25/100        # How much the status changes each step

    
    lst = string.split()
    # TODO: make it also check all are numbers
    if(len(lst) < BUTTON_NUM):          # stop processing if list incomplete
        return

    for i in range(BUTTON_NUM):
        if int(lst[i]) > threshold + deadZone:
            status[Qnum][i] += statStep
        elif int(lst[i]) < threshold - deadZone:
            status[Qnum][i] += - statStep
        status[Qnum][i] = max( min(1, status[Qnum][i]), 0)

        if status[Qnum][i] == 1 and canVote[Qnum][i]:
            votes[Qnum][i]+=1
            canVote[Qnum][i] = False
            # A vote was just cast
        elif status[Qnum][i] == 0:
            canVote[Qnum][i] = True
            # A button was just reset
    divGraph.update(votes[Qnum], status[Qnum], canVote[Qnum])
    barStatus.update( votes[Qnum], status[Qnum], canVote[Qnum])


    
#make our own buffer
#useful for parsing commands
#Serial.readline seems unreliable at times too
serBuffer = ""

def readSerial():
    global serBuffer    # get the buffer from outside of this function
    
    while True:
        c = ser.read() # attempt to read a character from Serial

        if len(c) == 0:         #was anything read?
            break
                            
        if c == b'\n':
            serBuffer += "\n" # add the newline to the buffer

            #add the line to the TOP of the log
            log.insert('0.0', serBuffer)
            #update(serBuffer)
            updateAll(serBuffer)
            serBuffer = "" # empty the buffer
        else:
            serBuffer += c.decode("utf-8")  # add to the buffer

    root.after(2, readSerial) # check serial again soon


# after initializing serial, an arduino may need a bit of time to reset
root.after(200, readSerial)

root.mainloop()
