/* LIBRARY INCLUDES */

#include <SerialCommand.h>
#include <Stdio.h>
#include <PciManager.h>
#include <PciListenerImp.h>


/* AVR (ATMEGA328P-PU) PIN DEFINITIONS */

const int TOPLED_RED = 9;
const int TOPLED_GREEN = 10;
const int TOPLED_BLUE = 11;

const int BOTTOMLED_RED = 4;
const int BOTTOMLED_GREEN = 5;
const int BOTTOMLED_BLUE = 6;

const int LEFTEAR_MOTOR = 12;
const int LEFTEAR_IRLED = 7;
const int LEFTEAR_INTERRUPT = 1;

const int RIGHTEAR_MOTOR = 13;
const int RIGHTEAR_IRLED = 8;
const int RIGHTEAR_INTERRUPT = 0;

const int HEADBUTTON_INTERRUPT = A2;


/* CONSTANTS */

const char TOP = 'T';
const char BOTTOM = 'B';
const char LEFT = 'L';
const char RIGHT = 'R';
const int ZERO_EAR_POS = 0;


/* GLOBAL VARIABLES */

volatile int leftPinPosition;
volatile int leftEarTargetPosition;
volatile long leftInterruptTime;
volatile long leftLastInterruptTime;
volatile long leftPulseWidth;
volatile boolean seenLeftGap;

volatile int rightPinPosition;
volatile int rightEarTargetPosition;
volatile long rightInterruptTime;
volatile long rightLastInterruptTime;
volatile long rightPulseWidth;
volatile boolean seenRightGap;

PciListenerImp listener(HEADBUTTON_INTERRUPT, buttonPress);
SerialCommand serialCommand;

/*
Setup initialises:
- The I/O for control of the ears and LEDs
- The functions to handle serial commands
- The IR LEDs for the rotary encoders
- The serial port
*/
void setup() {
	// Set Output Pins
	pinMode(TOPLED_RED, OUTPUT);
	pinMode(TOPLED_GREEN, OUTPUT);
	pinMode(TOPLED_BLUE, OUTPUT);

	pinMode(BOTTOMLED_RED, OUTPUT);
	pinMode(BOTTOMLED_GREEN, OUTPUT);
	pinMode(BOTTOMLED_BLUE, OUTPUT);

	pinMode(LEFTEAR_MOTOR, OUTPUT);
	pinMode(LEFTEAR_IRLED, OUTPUT);

	pinMode(RIGHTEAR_MOTOR, OUTPUT);
	pinMode(RIGHTEAR_IRLED, OUTPUT);

	// Add Serial Handlers
	serialCommand.addCommand("LED", LED);
	serialCommand.addCommand("EARMOV", EARMOV);
	serialCommand.setDefaultHandler(INVALID);

	// Turn on IR LED for Rotary Encoders
	digitalWrite(LEFTEAR_IRLED, HIGH);
	digitalWrite(RIGHTEAR_IRLED, HIGH);

	// Start Serial communication at 9600bps
	Serial.begin(9600);

	// Set initial interrupt handlers to reset ears if moved
	attachInterrupt(LEFTEAR_INTERRUPT, leftEarMoved, CHANGE);
	attachInterrupt(RIGHTEAR_INTERRUPT, rightEarMoved, CHANGE);

    // Set Pin Change interrupt handler for button presses.
    PciManager.registerListener(HEADBUTTON_INTERRUPT, &listener);
}


/*
Main loop just listens for Serial Commands
*/
void loop() {
	serialCommand.readSerial();
}


/*
LED is called when receiving serial commands of the form:

LED [T|B] [0-255] [0-255] [0-255]
|		 |		 |       |
pos     R		 G		 B

The respective LED is set using the R, G & B values for PWM. 
*/
void LED() {
	char *arg;
	char ledPos;
	int redfreq;
	int greenfreq;
	int bluefreq;

	arg = serialCommand.next();
	if (arg != NULL) {
		ledPos = *arg;
	}

	arg = serialCommand.next();
	if (arg != NULL) {
		redfreq = atoi(arg); 
	}

	arg = serialCommand.next();
	if (arg != NULL) {
		greenfreq = atoi(arg); 
	}

	arg = serialCommand.next();
	if (arg != NULL) {
		bluefreq = atoi(arg); 
	}

	switch(ledPos){
		case TOP:
			analogWrite(TOPLED_RED, redfreq);
			analogWrite(TOPLED_GREEN, greenfreq);
			analogWrite(TOPLED_BLUE, bluefreq);
			break;
		case BOTTOM:
			analogWrite(BOTTOMLED_RED, redfreq);
			analogWrite(BOTTOMLED_GREEN, greenfreq);
			analogWrite(BOTTOMLED_BLUE, bluefreq);
			break;    
	}

}


/*
EARMOV is called when receiving serial commands of the form:

EARMOV [R|L] [0-17]
|     |
pos   pin

It unpacks the parameters and calls moveEar with the relevant
arguments.
*/
void EARMOV(){
	char *arg;
	char earSide;
	int targetPin;

	arg = serialCommand.next();
	if (arg != NULL) {
		earSide = *arg;
	}

	arg = serialCommand.next();
	if (arg != NULL) {
		targetPin = atoi(arg);
	}

	moveEar(earSide, targetPin);
}

/*
moveEar controls movement of an individual ear.
The correct interrupt for the ear is enabled, and
variables for correct functioning of the interrupt are set.
*/
void moveEar(char earSide, int targetPosition){
	int rotaryPin = (targetPosition + 2) % 17;
	switch(earSide){
		case LEFT:
			attachInterrupt(LEFTEAR_INTERRUPT, moveLeftEar, RISING);
			leftEarTargetPosition = rotaryPin;
			seenLeftGap = false;
			leftInterruptTime = millis();
			digitalWrite(LEFTEAR_MOTOR, HIGH);
			break;
		case RIGHT:
			attachInterrupt(RIGHTEAR_INTERRUPT, moveRightEar, RISING);
			rightEarTargetPosition = rotaryPin;
			seenRightGap = false;
			rightInterruptTime = millis();
			digitalWrite(RIGHTEAR_MOTOR, HIGH);  
			break;
	}
}


/*
Interrupt routine for setting the position of the left ear.
This takes into account the reference gap to ensure that the
pin position remains correct, e.g. 0-17 (inclusive)
*/
void moveLeftEar(){
	leftPinPosition++;

	leftLastInterruptTime = leftInterruptTime;
	leftInterruptTime = millis();

	leftPulseWidth = leftInterruptTime - leftLastInterruptTime;

	if(leftPulseWidth > 500){
		leftPinPosition = 0;
	}

	if(leftPinPosition == leftEarTargetPosition){
		digitalWrite(LEFTEAR_MOTOR, LOW);
		sendEarPosition(LEFT, leftPinPosition);
		attachInterrupt(LEFTEAR_INTERRUPT, leftEarMoved, RISING); 
	}
}


/*
Interrupt routine for setting the position of the right ear.
This takes into account the reference gap to ensure that the
pin position remains correct, e.g. 0-17 (inclusive)
*/
void moveRightEar(){
	rightPinPosition++;

	rightLastInterruptTime = rightInterruptTime;
	rightInterruptTime = millis();

	rightPulseWidth = rightInterruptTime - rightLastInterruptTime;

	if(rightPulseWidth > 500){
		rightPinPosition = 0;
	}

	if(rightPinPosition == rightEarTargetPosition){
		digitalWrite(RIGHTEAR_MOTOR, LOW);
		sendEarPosition(RIGHT, rightPinPosition);
		attachInterrupt(RIGHTEAR_INTERRUPT, rightEarMoved, RISING); 
	}
}


/*
sendEarPosition is used to report the ear position back over
the serial port upon successful positioning.
*/
void sendEarPosition(char earSide, int rotaryPin){
	int position = (rotaryPin - 2) % 17;
	char message[32];
	sprintf(message, "{\"ear\": \"%c\", \"pos\": %d}\n", earSide, position);
	Serial.print(message);
}


/*
Interrupt routine called when the right ear is moved manually.
It sends a message over the serial connection to say the ear
has been moved, then resets the ear to upright.
*/
void leftEarMoved(){
	Serial.print("{\"ear\": \"L\", \"moved\": 1}\n");
	moveEar(LEFT, ZERO_EAR_POS);
}


/*
Interrupt routine called when the right ear is moved manually.
It sends a message over the serial connection to say the ear
has been moved, then resets the ear to upright.
*/
void rightEarMoved(){
	Serial.print("{\"ear\": \"R\", \"moved\": 1}\n");
	moveEar(RIGHT, ZERO_EAR_POS);
}


/*
Interrupt routine called when the head button is pressed.
A serial message is sent to say the button was pressed, and
both ears are reset to upright. This function performs
software debouncing to ensure multiple events are not
triggered for a single button press.
*/
void buttonPress(byte changeKind) {
    static unsigned long last_interrupt_time = 0;
    unsigned long interrupt_time = millis();
    if (interrupt_time - last_interrupt_time > 200){
        Serial.print("{\"button\": 1}\n");
        moveEar(LEFT, ZERO_EAR_POS);
        moveEar(RIGHT, ZERO_EAR_POS);
    }
    last_interrupt_time = interrupt_time;
}


/*
INVALID is called when the serial command given doesn't match 
any available functions.
*/
void INVALID(const char *command) {
	Serial.print("{\"invalid\": 1}\n");
}
